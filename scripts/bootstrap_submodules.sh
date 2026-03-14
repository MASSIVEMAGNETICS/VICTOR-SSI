#!/usr/bin/env bash
# scripts/bootstrap_submodules.sh
# Bootstraps MASSIVEMAGNETICS component repositories.
#
# --method=submodule  (default) Adds repos as git submodules under ./components/
# --method=clone               Clones repos as sibling directories (../NAME)
#
# Usage:
#   ./scripts/bootstrap_submodules.sh --method=submodule
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

# Component repositories (SSH URLs)
declare -A REPOS
REPOS["ragflow"]="git@github.com:MASSIVEMAGNETICS/ragflow.git"
REPOS["conscious-river"]="git@github.com:MASSIVEMAGNETICS/conscious-river.git"
REPOS["Liquidation-Analysis-using-Multi-Agent-Reinforcement-Learning-ICML-2019"]="git@github.com:MASSIVEMAGNETICS/Liquidation-Analysis-using-Multi-Agent-Reinforcement-Learning-ICML-2019.git"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Bootstrap method: $METHOD"
echo "==> Bootstrapping ${#REPOS[@]} component repositories..."

if [ "$METHOD" = "clone" ]; then
  # Clone as sibling directories (docker-compose.yml references ../NAME)
  echo "Cloning component repos as sibling directories (requires SSH access)"
  PARENT_DIR="$(dirname "$REPO_ROOT")"
  for NAME in "${!REPOS[@]}"; do
    URL="${REPOS[$NAME]}"
    TARGET="$PARENT_DIR/$NAME"
    if [ -d "$TARGET" ]; then
      echo "  [skip] $NAME already exists at $TARGET"
    else
      echo "  [clone] $URL -> $TARGET"
      git clone "$URL" "$TARGET"
    fi
  done
  echo ""
  echo "    Component directories:"
  for NAME in "${!REPOS[@]}"; do
    echo "    - $PARENT_DIR/$NAME"
  done
else
  # Add as git submodules under components/ (within repo tree)
  echo "Adding component repositories as git submodules under ./components/"
  cd "$REPO_ROOT"
  mkdir -p components
  for NAME in "${!REPOS[@]}"; do
    URL="${REPOS[$NAME]}"
    SUBMODULE_PATH="components/$NAME"
    if [ -d "$SUBMODULE_PATH/.git" ] || grep -q "path = $SUBMODULE_PATH" .gitmodules 2>/dev/null; then
      echo "  [skip] submodule $NAME already registered at $SUBMODULE_PATH"
    else
      echo "  [add submodule] $NAME -> $SUBMODULE_PATH"
      git submodule add "$URL" "$SUBMODULE_PATH" || true
    fi
  done
  echo "==> Updating all submodules..."
  git submodule update --init --recursive
  echo ""
  echo "    NOTE: When using --method=submodule, update docker-compose.yml"
  echo "    build contexts from '../NAME' to './components/NAME'."
  echo ""
  echo "    Component directories:"
  for NAME in "${!REPOS[@]}"; do
    echo "    - $REPO_ROOT/components/$NAME"
  done
fi

echo ""
echo "==> Bootstrap complete!"
echo "    Next: cp .env.example .env && docker-compose up --build"
