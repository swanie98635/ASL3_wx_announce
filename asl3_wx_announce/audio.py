import os
import subprocess
import logging
import time
import shutil
from typing import List

class AudioHandler:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Default to echo if no TTS configured (just for safety)
        self.tts_template = config.get('voice', {}).get('tts_command', 'echo "{text}" > {file}')
        self.tmp_dir = "/tmp/asl3_wx"
        os.makedirs(self.tmp_dir, exist_ok=True)
        # Asterisk sounds directory
        self.asterisk_sounds_dir = "/usr/share/asterisk/sounds/en"

    def generate_audio(self, text: str, filename: str = "announcement.gsm") -> List[tuple[str, float]]:
        # Sanitize text to prevent shell injection/breaking
        text = text.replace('"', "'").replace('`', '').replace('(', '').replace(')', '')
        
        # Check for pause delimiter
        segments = text.split('[PAUSE]')
        
        # Clean up empty segments
        segments = [s.strip() for s in segments if s.strip()]
        
        if not segments:
            raise Exception("No text to generate")

        final_files = []
        
        try:
            # Generate separate files for each segment
            for i, segment in enumerate(segments):
                # 1. Generate Raw WAV
                raw_filename = f"raw_{os.path.splitext(filename)[0]}_{i}.wav"
                raw_path = os.path.join(self.tmp_dir, raw_filename)
                
                # Cleanup
                if os.path.exists(raw_path):
                    os.remove(raw_path)

                cmd = self.tts_template.format(file=raw_path, text=segment)
                self.logger.info(f"Generating segment {i}: {cmd}")
                subprocess.run(cmd, shell=True, check=True)
                
                if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
                    raise Exception(f"TTS failed for segment {i}")
                
                # Get Duration from WAV (Reliable)
                duration = self.get_audio_duration(raw_path)
                
                # 2. Convert to ASL3 format (GSM)
                gsm_filename = f"asl3_wx_{os.path.splitext(filename)[0]}_{i}.gsm"
                gsm_tmp_path = os.path.join(self.tmp_dir, gsm_filename)
                
                self.convert_audio(raw_path, gsm_tmp_path)
                
                # 3. Move to Asterisk Sounds Directory
                dest_path = os.path.join(self.asterisk_sounds_dir, gsm_filename)
                
                move_cmd = f"sudo mv {gsm_tmp_path} {dest_path}"
                self.logger.info(f"Moving to sounds dir: {move_cmd}")
                subprocess.run(move_cmd, shell=True, check=True)
                
                # 4. Fix permissions
                chmod_cmd = f"sudo chmod 644 {dest_path}"
                subprocess.run(chmod_cmd, shell=True, check=True)
                
                final_files.append((dest_path, duration))
            
            return final_files
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Audio Generation Failed: {e}")
            raise e
        except Exception as e:
            self.logger.error(f"Error: {e}")
            raise e

    def convert_audio(self, input_path: str, output_path: str):
        """
        Convert audio to 8000Hz, 1 channel, 16-bit signed integer PCM wav.
        """
        # cleanup prior if exists
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except OSError:
            pass
            
        cmd = f"sox {input_path} -r 8000 -c 1 -t gsm {output_path}"
        self.logger.info(f"Converting audio: {cmd}")
        subprocess.run(cmd, shell=True, check=True)

    def get_audio_duration(self, filepath: str) -> float:
        try:
            # use sox to get duration
            cmd = f"sox --i -D {filepath}"
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            self.logger.error(f"Failed to get duration for {filepath}: {e}")
            return 0.0

    def play_on_nodes(self, audio_segments: List[tuple[str, float]], nodes: List[str]):
        # Iterate through segments
        for i, (filepath, duration) in enumerate(audio_segments):
            filename = os.path.basename(filepath)
            name_no_ext = os.path.splitext(filename)[0]
            
            self.logger.info(f"Segment {i} duration: {duration}s")
            
            # Play on all nodes (simultaneously-ish)
            for node in nodes:
                asterisk_cmd = f'sudo /usr/sbin/asterisk -rx "rpt playback {node} {name_no_ext}"'
                self.logger.info(f"Playing segment {i} on {node}: {asterisk_cmd}")
                try:
                    subprocess.run(asterisk_cmd, shell=True, check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Playback failed on {node}. Return code: {e.returncode}")
                    self.logger.error(f"Stdout: {e.stdout}")
                    self.logger.error(f"Stderr: {e.stderr}")
            
            # Wait for playback to finish + buffer
            # Safe buffer: 1.5s
            time.sleep(duration + 1.5)
            
            # Wait for 5 seconds between segments (but not after the last one)
            if i < len(audio_segments) - 1:
                self.logger.info("Pausing 5s for unkey...")
                time.sleep(5)

    def ensure_alert_tone(self) -> tuple[str, float]:
        """
        Generates the 2-second alternating alert tone if it doesn't exist.
        Returns (filepath, duration)
        """
        filename = "alert_tone.gsm"
        dest_path = os.path.join(self.asterisk_sounds_dir, filename)
        
        # We assume 2.0s duration for the generated tone
        duration = 2.0
        
        # Check if already exists (skip regen to save time/writes)
        if os.path.exists(dest_path):
            return (dest_path, duration)
            
        self.logger.info("Generating Alert Tone...")
        
        raw_filename = "raw_alert_tone.wav"
        raw_path = os.path.join(self.tmp_dir, raw_filename)
        
        # Generate Hi-Lo Siren: 0.25s High, 0.25s Low, repeated 3 times (total 4 cycles = 2s)
        # 1000Hz and 800Hz
        cmd = f"sox -n -r 8000 -c 1 {raw_path} synth 0.25 sine 1000 0.25 sine 800 repeat 3"
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            
            # Convert to GSM
            gsm_tmp_path = os.path.join(self.tmp_dir, filename)
            self.convert_audio(raw_path, gsm_tmp_path)
            
            # Move to Asterisk Dir
            move_cmd = f"sudo mv {gsm_tmp_path} {dest_path}"
            subprocess.run(move_cmd, shell=True, check=True)
            
            # Fix permissions
            chmod_cmd = f"sudo chmod 644 {dest_path}"
            subprocess.run(chmod_cmd, shell=True, check=True)
            
            return (dest_path, duration)
            
        except Exception as e:
            self.logger.error(f"Failed to generate alert tone: {e}")
            raise e
