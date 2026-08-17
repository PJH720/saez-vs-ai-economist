#!/usr/bin/env bash
#
# Prepare the environment for the E1-E5 harness.
#
#   1. Clone salesforce/ai-economist at the exact commit the results were
#      produced against, into ./ai-economist -- the path experiments/compat.py
#      hardcodes. Nothing in that tree is patched.
#   2. Create .venv and install the verified-minimal dependency set.
#
# Idempotent: safe to re-run.

set -euo pipefail

# The commit the committed results were produced against.
# Pinned rather than tracking master, so the numbers stay checkable.
PINNED_SHA="a84d5f3fdcabb207d9fde7754d34906903b3e184"
UPSTREAM_URL="https://github.com/salesforce/ai-economist.git"

cd "$(dirname "$0")"

# --- 1. upstream ------------------------------------------------------------
# compat.py resolves REPO_ROOT as <this dir>/ai-economist. The clone must land
# there exactly, or the env layout file (quadrant_25x25_20each_30clump.txt) will
# not resolve and E1 dies during env construction.
if [ ! -d ai-economist/.git ]; then
  echo "==> Cloning salesforce/ai-economist"
  git clone --quiet "$UPSTREAM_URL" ai-economist
else
  echo "==> ai-economist/ already present"
  git -C ai-economist fetch --quiet origin
fi

echo "==> Checking out pinned commit ${PINNED_SHA:0:10}"
git -C ai-economist checkout --quiet "$PINNED_SHA"

# The repo's central claim is that upstream is called unmodified. Verify it here
# rather than merely asserting it in the README.
if [ -n "$(git -C ai-economist status --porcelain --untracked-files=no)" ]; then
  echo "!! upstream working tree has modifications -- results are not comparable" >&2
  git -C ai-economist status --short >&2
  exit 1
fi
echo "    upstream tree is clean and at the pinned commit"

# --- 2. environment ---------------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
  echo "!! uv not found. Install it: https://docs.astral.sh/uv/  (or use requirements.txt with pip)" >&2
  exit 1
fi

echo "==> Creating .venv and installing dependencies"
uv sync --quiet

# --- 3. font advisory -------------------------------------------------------
# Figure labels are bilingual Korean/English. Without a CJK font, matplotlib
# renders the Korean half as tofu boxes. This affects rendering only -- every
# number the harness reports is unaffected.
if ! .venv/bin/python - <<'PY'
import sys
from matplotlib import font_manager
installed = {f.name for f in font_manager.fontManager.ttflist}
sys.exit(0 if installed & {"Noto Sans CJK KR", "Noto Serif CJK KR", "NanumGothic"} else 1)
PY
then
  echo ""
  echo "    NOTE: no CJK font found. Figures will regenerate with Korean labels"
  echo "    as boxes; the numeric tables are unaffected. To match the committed"
  echo "    figures, install Noto Sans CJK KR or NanumGothic."
fi

cat <<'EOF'

Setup complete. Run the experiments (E5 must precede E3 -- E3 reads E5's output):

  cd experiments
  ../.venv/bin/python e1_saez_distribution.py
  ../.venv/bin/python e2_saez_elasticity.py
  ../.venv/bin/python e4_tax_avoidance.py
  ../.venv/bin/python e5_mini_ai_economist.py
  ../.venv/bin/python e3_welfare_functions.py
  cd ..

Then confirm nothing drifted -- from the repo root, not from experiments/
(from there the path becomes experiments/experiments/results/ and git aborts
with "fatal: ambiguous argument"):

  git diff --stat experiments/results/     # expect empty
EOF
