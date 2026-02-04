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

        # Resolve language code
        lang_cfg = self.config.get('language', 'en')
        lang_map = {
            'en': 'en-US',
            'fr': 'fr-FR'
        }
        lang_code = lang_map.get(lang_cfg, 'en-US')
            
        cmd = self.tts_template.format(file=filepath, text=text, lang=lang_code)
        self.logger.info(f"Generating audio: {cmd}")
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            return filepath
        except subprocess.CalledProcessError as e:
            self.logger.error(f"TTS Failed: {e}")
            raise e

    def play_on_nodes(self, filepath: str, nodes: List[str]):
        # Asterisk usually wants paths relative to the sounds directory if they are inside it.
        # e.g. "rpt localplay <node> asl3_wx_announce/report"
        
        path_no_ext = os.path.splitext(filepath)[0]
        
        # Standard sounds root
        sounds_root = "/var/lib/asterisk/sounds/"
        
        if path_no_ext.startswith(sounds_root):
            # Strip root: /var/lib/asterisk/sounds/dir/file -> dir/file
            play_path = path_no_ext[len(sounds_root):]
            # Ensure no leading slash
            if play_path.startswith("/"):
                play_path = play_path[1:]
        else:
            # Outside standard dir, use absolute
            play_path = path_no_ext
        
        for node in nodes:
            asterisk_cmd = f'asterisk -rx "rpt localplay {node} {play_path}"'
            self.logger.info(f"Playing on {node}: {asterisk_cmd}")
            try:
                subprocess.run(asterisk_cmd, shell=True, check=True)
            except Exception as e:
                self.logger.error(f"Playback failed on {node}: {e}")
