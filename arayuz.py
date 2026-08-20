import sys

sys.dont_write_bytecode = True

from ultron.ui.arayuz import JarvisApp, main  # noqa: E402

__all__ = ["JarvisApp", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
