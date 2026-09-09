"""Compat alias — canonical entry is androidlife_report.py."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("androidlife_report.py")), run_name="__main__")
