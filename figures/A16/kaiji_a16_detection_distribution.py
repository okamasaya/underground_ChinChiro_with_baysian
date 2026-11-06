"""Regenerate the detection-distribution figure from the bundled exact data."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'analysis'))
from discussion_figures import make_a16
if __name__=='__main__':
    make_a16()
