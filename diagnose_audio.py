import subprocess
import os
import sys
import shutil

# Configuration
TEST_NODE = "your node here" # User confirmed this node
TONE_FILE = "/tmp/test_tone.wav"
FINAL_TONE_FILE = "/var/lib/asterisk/sounds/test_tone.wav"
TTS_FILE = "/tmp/test_tts.wav"
FINAL_TTS_FILE = "/var/lib/asterisk/sounds/test_tts.wav"

def run_cmd(cmd, description):
    print(f"[{description}] Executing: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False, e.stderr

def main():
    print("=== ASL3 Audio Diagnostic ===")
    
    # 1. Check Tools
    print("\n--- Checking Tools ---")
    tools = ["sox", "pico2wave", "asterisk"]
    for tool in tools:
        if shutil.which(tool) or os.path.exists(f"/usr/sbin/{tool}") or os.path.exists(f"/usr/bin/{tool}"):
            print(f"OK: {tool} found")
        else:
            print(f"WARNING: {tool} not found in PATH")

    # 2. Test Tone Generation (Isolates TTS)
    print("\n--- Test 1: Pure Tone Generation ---")
    # Generate 1kHz sine wave for 3 seconds
    cmd = f"sox -n -r 8000 -c 1 -b 16 -e signed-integer {TONE_FILE} synth 3 sine 1000"
    success, _ = run_cmd(cmd, "Generating Tone")
    
    if success:
        if os.path.getsize(TONE_FILE) > 0:
            print(f"OK: Tone file created ({os.path.getsize(TONE_FILE)} bytes)")
        else:
            print("FAIL: Tone file is empty")
            return

        # Move to Asterisk Sounds
        run_cmd(f"sudo mv {TONE_FILE} {FINAL_TONE_FILE}", "Installing Tone File")
        run_cmd(f"sudo chmod 644 {FINAL_TONE_FILE}", "Setting Permissions")
        
        # Playback
        print(f"Attempting playback on node {TEST_NODE}...")
        play_cmd = f"sudo /usr/sbin/asterisk -rx 'rpt playback {TEST_NODE} test_tone'"
        p_success, _ = run_cmd(play_cmd, "Playing Tone")
        if p_success:
            print(">>> LISTEN NOW: You should hear a 3-second beep.")
        else:
            print("FAIL: Playback command failed")
    
    input("\nPress Enter to continue to TTS test (or Ctrl+C to stop)...")

    # 3. Test TTS Generation
    print("\n--- Test 2: TTS Generation ---")
    text = "Audio test. One two three."
    cmd = f"pico2wave -w {TTS_FILE} \"{text}\""
    success, _ = run_cmd(cmd, "Generating TTS")
    
    if success:
        # Check size
        if os.path.exists(TTS_FILE) and os.path.getsize(TTS_FILE) > 100:
             print(f"OK: TTS file created ({os.path.getsize(TTS_FILE)} bytes)")
             
             # Convert
             conv_cmd = f"sox {TTS_FILE} -r 8000 -c 1 -b 16 -e signed-integer {FINAL_TTS_FILE}"
             run_cmd(conv_cmd, "Converting & Installing TTS")
             run_cmd(f"sudo chmod 644 {FINAL_TTS_FILE}", "Permissions")
             
             # Playback
             print(f"Attempting playback on node {TEST_NODE}...")
             play_cmd = f"sudo /usr/sbin/asterisk -rx 'rpt playback {TEST_NODE} test_tts'"
             run_cmd(play_cmd, "Playing TTS")
             print(">>> LISTEN NOW: You should hear 'Audio test, one two three'.")
        else:
             print("FAIL: TTS file missing or too small")

    print("\n=== Diagnostic Complete ===")

if __name__ == "__main__":
    main()
