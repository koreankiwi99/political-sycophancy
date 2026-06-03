# Prompts

All LLM prompts live here as plain `.txt` files. Code imports them via the small loader in `prompts/__init__.py` (or with `pathlib.Path("prompts/<name>.txt").read_text()` for ad-hoc scripts).

Templates use Python `str.format()` placeholders (`{paragraph}`, etc.). The code is responsible for passing the right keys.

| File | Used by | Type | Inputs |
|---|---|---|---|
| `extract_atomic_facts.txt` | `pipeline/extract/extract_pipeline.py` | system message | (paragraph is passed as the user message, not interpolated) |
| `perturb_v1_intention_driven.txt` | `pipeline/perturb/pilot_intention_driven.py` | user message | `{paragraph}` |
| `perturb_v2_answerable.txt` | `pipeline/perturb/pilot_v2_answerable.py` (current canonical) | user message | `{paragraph}` |

When iterating on a prompt:
1. Copy `perturb_v2_answerable.txt` → `perturb_v3_<change>.txt`.
2. Edit the new file.
3. Point one pilot script at the new file (change `PROMPT_PATH`).
4. Don't overwrite v2 until v3 is validated.
