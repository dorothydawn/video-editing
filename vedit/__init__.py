"""vedit — code-driven editing for short-form reels and long-form YouTube videos."""
from pathlib import Path

__version__ = "0.1.0"

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"
MODELS = ASSETS / "models"
SFX = ASSETS / "sfx"
