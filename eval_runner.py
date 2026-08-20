import sys

sys.dont_write_bytecode = True

from ultron.evaluation.eval_runner import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
