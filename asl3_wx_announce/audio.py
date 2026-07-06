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
        self.tts_template = config.get('voice', {}).get('tts_command', 'echo "{text}" > {file}')
        self.tmp_dir = "/tmp/asl3_wx"
        os.makedirs(self.tmp_dir, exist_ok=True)
        # Asterisk sounds directory
        self.asterisk_sounds_dir = "/usr/share/asterisk/sounds/en"

    def generate_audio(self, text: str, filename: str = "announcement.gsm") -> List[tuple[str, float]]:
        text = text.replace('"', "'").replace('`', '').replace('(', '').replace(')', '')
        
        # Check for pause delimiter
        segments = text.split('[PAUSE]')
        segments = [s.strip() for s in segments if s.strip()]
        
        if not segments:
            raise Exception("No text to generate")

        final_files = []
        
        try:
            for i, segment in enumerate(segments):
                raw_filename = f"raw_{os.path.splitext(filename)[0]}_{i}.wav"
                raw_path = os.path.join(self.tmp_dir, raw_filename)
                
                if os.path.exists(raw_path):
                    os.remove(raw_path)

                cmd = self.tts_template.format(file=raw_path, text=segment)
                self.logger.info(f"Generating segment {i}: {cmd}")
                subprocess.run(cmd, shell=True, check=True)
                
                if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
                    raise Exception(f"TTS failed for segment {i}")
                
                duration = self.get_audio_duration(raw_path)
                
                gsm_filename = f"asl3_wx_{os.path.splitext(filename)[0]}_{i}.gsm"
                gsm_tmp_path = os.path.join(self.tmp_dir, gsm_filename)
                
                self.convert_audio(raw_path, gsm_tmp_path)
                
                dest_path = os.path.join(self.asterisk_sounds_dir, gsm_filename)
                
                move_cmd = f"sudo mv {gsm_tmp_path} {dest_path}"
                self.logger.info(f"Moving to sounds dir: {move_cmd}")
                subprocess.run(move_cmd, shell=True, check=True)
                
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
            cmd = f"sox --i -D {filepath}"
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            self.logger.error(f"Failed to get duration for {filepath}: {e}")
            return 0.0

    def play_on_nodes(self, audio_segments: List[tuple[str, float]], nodes: List[str]):
        for i, (filepath, duration) in enumerate(audio_segments):
            filename = os.path.basename(filepath)
            name_no_ext = os.path.splitext(filename)[0]
            
            self.logger.info(f"Segment {i} duration: {duration}s")
            
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
            time.sleep(duration + 1.5)
            
            # Wait for 45 seconds between segments (but not after the last one)
            if i < len(audio_segments) - 1:
                self.logger.info("Pausing 45s for unkey...")
                time.sleep(45)

    def ensure_alert_tone(self) -> tuple[str, float]:
        filename = "alert_tone.gsm"
        dest_path = os.path.join(self.asterisk_sounds_dir, filename)
        duration = 2.0
        
        if os.path.exists(dest_path):
            return (dest_path, duration)
            
        self.logger.info("Generating Alert Tone...")
        
        raw_filename = "raw_alert_tone.wav"
        raw_path = os.path.join(self.tmp_dir, raw_filename)
        cmd = f"sox -n -r 8000 -c 1 {raw_path} synth 0.25 sine 1000 0.25 sine 800 repeat 3"
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            gsm_tmp_path = os.path.join(self.tmp_dir, filename)
            self.convert_audio(raw_path, gsm_tmp_path)
            
            move_cmd = f"sudo mv {gsm_tmp_path} {dest_path}"
            subprocess.run(move_cmd, shell=True, check=True)
            
            chmod_cmd = f"sudo chmod 644 {dest_path}"
            subprocess.run(chmod_cmd, shell=True, check=True)
            
            return (dest_path, duration)
            
        except Exception as e:
            self.logger.error(f"Failed to generate alert tone: {e}")
            raise e
