"""Brand kits: brands/<name>/brand.json is the single source of truth for a client's look and sound.
Specs opt in with "brand": "<name>"; anything the spec sets explicitly still wins."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from . import ROOT, SFX

BRANDS = ROOT / "brands"


@lru_cache(None)
def load(name: str) -> dict:
    path = BRANDS / name / "brand.json"
    if not path.exists():
        raise SystemExit(f"no brand kit at {path}")
    return json.loads(path.read_text())


def hex_of(brand: dict, key: str) -> str:
    c = brand["colors"][key]
    return c["hex"] if isinstance(c, dict) else c


def rgb(brand: dict, key: str) -> tuple[int, int, int]:
    h = hex_of(brand, key).lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def caption_cfg(brand: dict | None, spec_cfg) -> dict | None:
    """Brand caption defaults under the spec's own caption settings."""
    if not spec_cfg:
        return spec_cfg
    base = dict(brand.get("captions", {})) if brand else {}
    if isinstance(spec_cfg, dict):
        if "style" in spec_cfg and spec_cfg["style"] != base.get("style"):
            base = {k: v for k, v in base.items() if k in ("font", "color", "highlight", "emphasis_color")}
        base.update(spec_cfg)
    return base


def text_overrides(brand: dict | None, style: str, spec_override: dict | None) -> dict:
    base = dict((brand or {}).get("text_styles", {}).get(style, {}))
    base.update(spec_override or {})
    return base


def sfx_path(brand: dict | None, cue: str) -> Path:
    """Resolve a named sound cue (pop, whoosh, ...) via the brand's sound palette, else the bundled pack."""
    rel = (brand or {}).get("sfx", {}).get(cue)
    if rel:
        return (ROOT / rel).resolve()
    return SFX / f"{cue}.wav"
