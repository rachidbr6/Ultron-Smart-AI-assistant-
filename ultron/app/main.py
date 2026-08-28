"""Application entrypoint for Open J.A.R.V.I.S."""

from __future__ import annotations

import argparse
import sys

for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

from ultron.runtime.jarvis_runtime import set_ui_callback, start_jarvis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Open J.A.R.V.I.S terminal assistant.")
    parser.add_argument("--version", action="store_true", help="print the package version and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print("Open J.A.R.V.I.S 1.0.0")
        return 0
    start_jarvis()
    return 0


__all__ = ["build_parser", "main", "set_ui_callback", "start_jarvis"]


if __name__ == "__main__":
    raise SystemExit(main())
