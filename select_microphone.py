#!/usr/bin/env python3
"""Select the best microphone and test it."""

import sounddevice as sd
import numpy as np

print("🎤 Microphone Selector")
print("=" * 60)

# List devices
devices = sd.query_devices()
input_devices = []

for i, device in enumerate(devices):
    if device['max_input_channels'] > 0:
        input_devices.append((i, device['name']))
        print(f"  [{len(input_devices)-1}] Device #{i}: {device['name']}")

print("\n📝 Which microphone should we test?")
print("   (Usually choose the 'Realtek' or 'Mic input' option)")

try:
    choice = input("\nEnter number (0-{}): ".format(len(input_devices)-1))
    device_idx = input_devices[int(choice)][0]
    device_name = input_devices[int(choice)][1]
    
    print(f"\n✅ Selected: {device_name} (Device #{device_idx})")
    
    print("\n🔴 Recording for 5 seconds... SPEAK LOUDLY AND CLEARLY NOW!")
    
    # Record with this device
    audio = sd.rec(int(16000 * 5), samplerate=16000, channels=1, dtype='int16', device=device_idx)
    sd.wait()
    
    # Check volume
    volume = np.abs(audio).mean()
    print(f"\n✅ Recording complete!")
    print(f"   Volume level: {volume:.1f}")
    
    if volume < 100:
        print(f"   ⚠️  PROBLEM: Volume is too low!")
        print(f"   💡 FIX: Increase microphone volume in Windows")
        print(f"      Right-click speaker → Volume mixer")
    elif volume > 500:
        print(f"   ✅ EXCELLENT: Volume is perfect! Jarvis should hear you.")
    else:
        print(f"   ℹ️  Moderate volume - should work")
    
    print(f"\n💾 Best microphone device: {device_idx}")
    print(f"   Add this to jarvis: set JARVIS_MICROPHONE_DEVICE={device_idx}")
    
except (ValueError, IndexError):
    print("❌ Invalid choice!")

