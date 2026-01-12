import os
import subprocess
import logging
from typing import List

class AudioHandler:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Default to echo if no TTS configured (just for safety)
        self.tts_template = config.get('voice', {}).get('tts_command', 'echo "{text}" > {file}')
        # Use standard Asterisk sounds directory
        self.output_dir = "/var/lib/asterisk/sounds/asl3_wx_announce"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_audio(self, text: str, filename: str = "announcement.wav") -> str:
        filepath = os.path.join(self.output_dir, filename)
        
        # Simple cleanup?
        if os.path.exists(filepath):
            os.remove(filepath)
            
        cmd = self.tts_template.format(file=filepath, text=text)
        self.logger.info(f"Generating audio: {cmd}")
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            return filepath
        except subprocess.CalledProcessError as e:
            self.logger.error(f"TTS Failed: {e}")
            raise e

    def play_on_nodes(self, filepath: str, nodes: List[str]):
        # Asterisk uses file path WITHOUT extension usually for play commands.
        # KD5FMU script uses absolute path successfully (e.g. /tmp/current-time)
        path_no_ext = os.path.splitext(filepath)[0]
        
        for node in nodes:
            asterisk_cmd = f'asterisk -rx "rpt localplay {node} {path_no_ext}"'
            self.logger.info(f"Playing on {node}: {asterisk_cmd}")
            try:
                subprocess.run(asterisk_cmd, shell=True, check=True)
            except Exception as e:
                self.logger.error(f"Playback failed on {node}: {e}")
