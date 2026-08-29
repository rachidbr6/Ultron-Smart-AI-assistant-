"""Install the "Orbitron" display font used by the ULTRON desktop UI.

Without this font installed, CustomTkinter silently falls back to a plain
default font for every title, header, and the large centerpiece wordmark -
the sci-fi look depends on it. Installs per-user (no admin rights needed).
Windows only.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/orbitron/Orbitron%5Bwght%5D.ttf"

INSTALL_SCRIPT = r"""
param([string]$FontPath)
$fontsDir = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
New-Item -ItemType Directory -Force -Path $fontsDir | Out-Null
$dest = Join-Path $fontsDir "Orbitron.ttf"
Copy-Item -Path $FontPath -Destination $dest -Force

Add-Type -AssemblyName System.Drawing
$collection = New-Object System.Drawing.Text.PrivateFontCollection
$collection.AddFontFile($dest)
$familyName = $collection.Families[0].Name

$regPath = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts"
New-ItemProperty -Path $regPath -Name "$familyName (TrueType)" -Value "Orbitron.ttf" -PropertyType String -Force | Out-Null

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class FontBroadcast {
    [DllImport("gdi32.dll")] public static extern int AddFontResource(string lpFileName);
    [DllImport("user32.dll")] public static extern int SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
}
"@
[FontBroadcast]::AddFontResource($dest) | Out-Null
[FontBroadcast]::SendMessage([IntPtr]0xffff, 0x001D, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
Write-Output "Installed font family: $familyName"
"""


def main() -> int:
    if sys.platform != "win32":
        print("This installer is Windows-only.")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        font_path = Path(tmp) / "orbitron.ttf"
        print(f"Downloading Orbitron from {FONT_URL} ...")
        urllib.request.urlretrieve(FONT_URL, font_path)

        script_path = Path(tmp) / "install_font.ps1"
        script_path.write_text(INSTALL_SCRIPT, encoding="utf-8")

        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path), "-FontPath", str(font_path)],
            capture_output=True,
            text=True,
        )
        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
            return 1

    print("Done. Restart the ULTRON app for the new font to take effect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
