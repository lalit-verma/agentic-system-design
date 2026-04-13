#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Install the agentic-systems-architect skill into a folder-based skill registry.

Usage:
  ./agentic-systems-architect/install-skill.sh --target /path/to/skills [--copy|--link] [--force]

Options:
  --target PATH  Directory that should contain the installed skill folder.
  --copy         Copy the skill folder into the target directory. Default.
  --link         Symlink the skill folder into the target directory.
  --force        Replace an existing installation at the destination path.
  -h, --help     Show this help message.
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="$(basename "$SCRIPT_DIR")"
TARGET_ROOT=""
MODE="copy"
FORCE="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_ROOT="${2:-}"
      shift 2
      ;;
    --copy)
      MODE="copy"
      shift
      ;;
    --link)
      MODE="link"
      shift
      ;;
    --force)
      FORCE="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$TARGET_ROOT" ]]; then
  echo "--target is required." >&2
  usage >&2
  exit 1
fi

mkdir -p "$TARGET_ROOT"

DESTINATION="${TARGET_ROOT%/}/${SKILL_NAME}"

if [[ -e "$DESTINATION" || -L "$DESTINATION" ]]; then
  if [[ "$FORCE" != "true" ]]; then
    echo "Destination already exists: $DESTINATION" >&2
    echo "Re-run with --force to replace it." >&2
    exit 1
  fi
  rm -rf "$DESTINATION"
fi

if [[ "$MODE" == "link" ]]; then
  ln -s "$SCRIPT_DIR" "$DESTINATION"
  echo "Symlinked $SKILL_NAME to $DESTINATION"
  exit 0
fi

mkdir -p "$DESTINATION"
cp -R "$SCRIPT_DIR"/. "$DESTINATION"
echo "Copied $SKILL_NAME to $DESTINATION"
