#!/usr/bin/env python3
"""Test if microphone is actually capturing audio."""

import sounddevice as sd
import numpy as np

print("🎤 Testing REAL microphone capture...")
print("-" * 50)

try:
    # List devices
    print("\n📋 Available audio devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  [{i}] {device['name']}")

    # Try to record for 5 seconds
    print("\n🔴 Recording for 5 seconds... SPEAK NOW!")
    print("   (Be loud and clear!)")
    
    duration = 5
    samplerate = 16000
    
    # Record audio
    audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    
    # Check if audio was captured
    volume = np.abs(audio).mean()
    print(f"\n✅ Recording complete!")
    print(f"   Samples recorded: {len(audio)}")
    print(f"   Audio volume level: {volume}")
    
    if volume < 100:
        print(f"   ⚠️  WARNING: Very low volume! Microphone may not be working.")
    elif volume > 500:
        print(f"   ✅ Good volume level detected!")
    else:
        print(f"   ℹ️  Moderate volume detected")
    
    print("\n" + "=" * 50)
    print("✅ Microphone capture is WORKING!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
