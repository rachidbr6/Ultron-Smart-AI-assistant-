#!/usr/bin/env python3
"""Launch Jarvis in lightweight mode (text-only, no wake-word listener)."""

import os
import sys

# Disable wake-word listener for lighter performance
os.environ["JARVIS_WAKE_WORD_ENABLED"] = "false"

# Disable voice input for minimal CPU
os.environ["JARVIS_VOICE_ENABLED"] = "false"

# Reduce energy threshold
os.environ["JARVIS_ENERGY_THRESHOLD"] = "300"

# Import and run Jarvis
from ultron.app.main import main

if __name__ == "__main__":
    print("🚀 Launching Jarvis in LIGHTWEIGHT mode (text-only)")
    print("   - Wake-word listener: DISABLED ✓ (reduced CPU)")
    print("   - Voice input: DISABLED ✓ (reduced CPU)")
    print("   - Voice output: Enabled (you can read responses)")
    print("   - UI input: Type commands directly in the window")
    print("   - CPU usage: MINIMAL\n")
    raise SystemExit(main())
