"""Tiny loader so callers can do `from prompts import load` / `load_pair` / `load_shared`.

Usage:
    from prompts import load, load_pair, load_shared

    # legacy single-prompt (v1/v2/v3):
    template = load("perturb_v2_answerable")
    msg = template.format(paragraph=text)

    # v4 paired system+user prompts:
    sys_tmpl, usr_tmpl = load_pair("v4a_screen")
    sys_msg = sys_tmpl.format(axes_definitions=load_shared("shared_axes"))
    usr_msg = usr_tmpl.format(paragraph=text)
"""
from __future__ import annotations
import pathlib

_DIR = pathlib.Path(__file__).resolve().parent


def load(name: str) -> str:
    """Read `prompts/<name>.txt` and return its contents."""
    p = _DIR / f"{name}.txt"
    if not p.exists():
        raise FileNotFoundError(f"prompt not found: {p}")
    return p.read_text(encoding="utf-8")


def load_pair(name: str) -> tuple[str, str]:
    """Return (system_template, user_template) for a paired prompt
    `<name>.system.txt` + `<name>.user.txt`."""
    return load(f"{name}.system"), load(f"{name}.user")


def load_shared(name: str) -> str:
    """Alias for `load`. Sugar for shared blocks (e.g., shared_axes)."""
    return load(name)
