"""Run this figure using the companion analysis module in the same bundle."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"analysis"))
from make_extension_figures import a21
if __name__=="__main__":
    a21()
