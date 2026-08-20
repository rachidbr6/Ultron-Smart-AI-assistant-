import sys

sys.dont_write_bytecode = True

from ultron.app.main import main, set_ui_callback, start_jarvis  # noqa: E402

__all__ = ["main", "start_jarvis", "set_ui_callback"]

if __name__ == "__main__":
    raise SystemExit(main())
