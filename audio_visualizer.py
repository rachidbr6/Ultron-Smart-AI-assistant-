#!/usr/bin/env python3
"""Real-time audio level visualizer to show if microphone is capturing sound."""

import sounddevice as sd
import numpy as np
import time

print("🎤 Real-Time Audio Level Monitor")
print("=" * 60)

# Find the best microphone
def find_best_mic():
    """Find the best available microphone."""
    devices = sd.query_devices()
    
    # Try devices in order of preference
    preferred_names = ['réseau de', 'microphone (realtek', 'microphone', 'mic']
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            name = device['name'].lower()
            for pref in preferred_names:
                if pref in name:
                    print(f"✅ Using: {device['name']} (Device #{i})")
                    return i
    
    print(f"⚠️  Using default microphone")
    return None

mic_device = find_best_mic()

print("Listening for sound... (Press Ctrl+C to stop)\n")

def audio_monitor():
    """Monitor audio in real-time and display levels."""
    
    # Create audio stream with specified device
    stream = sd.InputStream(channels=1, samplerate=16000, blocksize=1024, device=mic_device)
    stream.start()
    
    try:
        while True:
            # Read audio data
            data, _ = stream.read(1024)
            
            # Calculate volume
            volume = np.abs(data).mean()
            
            # Create visual bar
            bar_length = int(volume / 5)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            
            # Determine status
            if volume < 50:
                status = "🔇 Silent"
                color = "⚪"
            elif volume < 100:
                status = "🟢 Detecting sound..."
                color = "🟢"
            elif volume < 200:
                status = "🟡 Good volume"
                color = "🟡"
            else:
                status = "🔴 LOUD - Perfect!"
                color = "🔴"
            
            # Display
            print(f"\r{color} [{bar}] Volume: {volume:6.1f} | {status:30}", end="", flush=True)
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")
    finally:
        stream.stop()
        stream.close()

if __name__ == "__main__":
    print("📝 Instructions:")
    print("  1. Speak into your microphone NOW")
    print("  2. Watch the bar fill up as you make sound")
    print("  3. Green/Red bar = Jarvis CAN hear you!")
    print("  4. Empty bar = Jarvis CANNOT hear you")
    print("\n" + "=" * 60 + "\n")
    
    audio_monitor()
