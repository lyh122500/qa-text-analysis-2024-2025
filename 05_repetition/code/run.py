import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.argv.extend(["--stage", "repetition"])
    runpy.run_path(str(Path(__file__).resolve().parents[2] / "tools" / "run.py"), run_name="__main__")
