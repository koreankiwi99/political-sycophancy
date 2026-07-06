#!/usr/bin/env bash
# Fetch the raw World Bank corpus (~5.6 GB) needed only to REGENERATE items
# from scratch (Stage A). Re-scoring / re-running the eval on the shipped
# 110-item dataset does NOT need this.
#
# The corpus lives in a separate repo because it is too large for git:
#   koreankiwi99/wb-corpus-cache
#
# It is expected under data/worldbank-api/documents.jsonl (see
# pipeline/perturb/generate_v8_dataset.py:DOCS).
set -euo pipefail

DEST="$(cd "$(dirname "$0")/.." && pwd)/data"
REPO="${WB_CORPUS_REPO:-https://github.com/koreankiwi99/wb-corpus-cache.git}"

echo "Cloning $REPO → $DEST/wb-corpus-cache ..."
git clone --depth 1 "$REPO" "$DEST/wb-corpus-cache"

echo
echo "Done. Now place/symlink the extracted documents.jsonl so that"
echo "  $DEST/worldbank-api/documents.jsonl"
echo "exists (see the wb-corpus-cache README for its internal layout)."
