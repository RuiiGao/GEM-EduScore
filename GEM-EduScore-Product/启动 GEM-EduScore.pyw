"""Friendly Windows entry point; double-click this file to start the app."""

from pathlib import Path
from runpy import run_path


run_path(str(Path(__file__).with_name("GEM-EduScore Launcher.pyw")), run_name="__main__")
