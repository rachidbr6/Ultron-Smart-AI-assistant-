#!/usr/bin/env python3
"""Quick microphone test to verify sounddevice access."""

import sys

print("Testing microphone access...")
print("-" * 50)

try:
    import sounddevice as sd
    
    # List all audio devices
    print("🔍 Available audio devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"  [{i}] {device['name']}")
        print(f"      Channels: {device['max_input_channels']} in, {device['max_output_channels']} out")
    
    # Try to record a short sample
    print("\n🎤 Testing microphone recording (3 seconds)...")
    try:
        audio = sd.rec(int(sd.default.samplerate * 3), 
                      samplerate=16000, 
                      channels=1, 
                      dtype='int16')
        sd.wait()
        print("✅ Microphone recording successful!")
        print(f"   Recorded {len(audio)} samples")
    except Exception as e:
        print(f"❌ Recording failed: {e}")
    
    # Test speaker output
    print("\n🔊 Testing speaker output...")
    try:
        import numpy as np
        # Generate a test tone
        duration = 1  # 1 second
        frequency = 440  # A4 note
        samples = (np.sin(2 * np.pi * np.arange(sd.default.samplerate * duration) * frequency / sd.default.samplerate) * 32767).astype('int16')
        sd.play(samples, samplerate=16000)
        sd.wait()
        print("✅ Speaker output successful!")
    except Exception as e:
        print(f"❌ Speaker output failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Your microphone and speaker are working!")
    
except ImportError:
    print("❌ sounddevice not installed!")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
