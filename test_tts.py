import subprocess
import os
import sys

TEXT = "This is a test of the text to speech conversion. If you hear this, the text file conversion is working."
WAV_TMP = "/tmp/tts_test_raw.wav"
WAV_FINAL_PATH = "/var/lib/asterisk/sounds/tts_test_final.wav"
WAV_FINAL_NAME = "tts_test_final"
NODE = "62394"

def run(cmd):
    print(f"Executing: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def main():
    print("--- Starting TTS Isolation Test ---")
    
    # 1. Generate WAV from Text
    print(f"1. Generating audio for text: '{TEXT}'")
    run(f"pico2wave -w {WAV_TMP} \"{TEXT}\"")
    
    # 2. Convert to Asterisk format (8kHz, 16bit, Mono)
    print("2. Converting format with Sox...")
    # Clean up old file if exists
    if os.path.exists(WAV_FINAL_PATH):
        os.remove(WAV_FINAL_PATH)
        
    run(f"sox {WAV_TMP} -r 8000 -c 1 -b 16 -e signed-integer {WAV_FINAL_PATH}")
    
    # 3. Fix permissions
    print("3. Setting permissions...")
    os.chmod(WAV_FINAL_PATH, 0o644)
    
    # 4. Playback
    print(f"4. Playing on node {NODE}...")
    run(f"sudo /usr/sbin/asterisk -rx 'rpt playback {NODE} {WAV_FINAL_NAME}'")
    
    print("--- Test Complete ---")

if __name__ == "__main__":
    main()
