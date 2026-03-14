#!/usr/bin/env bash
# scripts/bootstrap_submodules.sh
# Bootstraps MASSIVEMAGNETICS component repositories either as git submodules
# (recommended) or as sibling directory clones.
#
# Usage:
#   ./scripts/bootstrap_submodules.sh --method=submodule   (default)
#   ./scripts/bootstrap_submodules.sh --method=clone

set -euo pipefail

METHOD="submodule"

for arg in "$@"; do
  case "$arg" in
    --method=submodule) METHOD="submodule" ;;
    --method=clone)     METHOD="clone" ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: $0 [--method=submodule|--method=clone]"
      exit 1
      ;;
  esac
done

# Component repositories to bootstrap (SSH URLs)
declare -A REPOS
REPOS["ragflow"]="git@github.com:MASSIVEMAGNETICS/ragflow.git"
REPOS["conscious-river"]="git@github.com:MASSIVEMAGNETICS/conscious-river.git"
REPOS["Liquidation-Analysis-using-Multi-Agent-Reinforcement-Learning-ICML-2019"]="git@github.com:MASSIVEMAGNETICS/Liquidation-Analysis-using-Multi-Agent-Reinforcement-Learning-ICML-2019.git"

echo "==> Bootstrap method: $METHOD"
echo "==> Bootstrapping ${#REPOS[@]} component repositories..."

if [ "$METHOD" = "clone" ]; then
  echo "Cloning component repos as sibling directories (requires SSH access)"
  PARENT_DIR="$(cd "$(dirname "$0")/.." && pwd)/.."
  for NAME in "${!REPOS[@]}"; do
    URL="${REPOS[$NAME]}"
    TARGET="$PARENT_DIR/$NAME"
    if [ -d "$TARGET" ]; then
      echo "  [skip] $NAME already exists at $TARGET"
    else
      echo "  [clone] $NAME -> $TARGET"
      git clone "$URL" "$TARGET"
    fi
  done
else
  echo "Adding component repositories as git submodules"
  REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  cd "$REPO_ROOT"
  for NAME in "${!REPOS[@]}"; do
    URL="${REPOS[$NAME]}"
    SUBMODULE_PATH="../$NAME"
    if git submodule status "$SUBMODULE_PATH" > /dev/null 2>&1; then
      echo "  [skip] submodule $NAME already registered"
    else
      echo "  [add submodule] $NAME"
      git submodule add "$URL" "$SUBMODULE_PATH" || true
    fi
  done
  echo "==> Updating all submodules..."
  git submodule update --init --recursive
fi

echo ""
echo "==> Bootstrap complete!"
echo "    Component directories expected at:"
for NAME in "${!REPOS[@]}"; do
  echo "    - ../$NAME"
done
echo ""
echo "    Next: cp .env.example .env && docker-compose up --build"
