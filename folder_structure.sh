#!/bin/bash
# A script to generate and copy a clean project directory structure to the clipboard.

# --- Configuration ---
# Directories and file patterns to exclude from the output. Add your own here.
EXCLUDE_PATTERNS=(
  "__pycache__"
  ".venv"
  ".git"
  "env"
  "venv"
  ".idea"
  "node_modules"
  ".DS_Store"
  "pgdata"       # Exclude PostgreSQL data directory
  "*.tgz"        # Exclude compressed archives
  "Chart.lock"   # Exclude Helm lock files
)

# --- Main Logic ---
# Exit immediately if a command exits with a non-zero status.
set -e

# Use the first argument as the project directory, or default to the current directory.
PROJECT_DIR="${1:-.}"

# --- Helper Functions ---

# Function to check for and install a command if missing.
ensure_command() {
  if ! command -v "$1" &>/dev/null; then
    echo "🟡 Command '$1' not found. Attempting to install..."
    if command -v brew &>/dev/null; then
      brew install "$1"
    elif command -v apt-get &>/dev/null; then
      sudo apt-get update && sudo apt-get install -y "$1"
    elif command -v dnf &>/dev/null; then
      sudo dnf install -y "$1"
    else
      echo "❌ Could not find a supported package manager (brew, apt-get, dnf). Please install '$1' manually." >&2
      exit 1
    fi
  fi
}

# Function to copy file content to the system clipboard.
copy_to_clipboard() {
  if command -v pbcopy &>/dev/null; then
    pbcopy < "$1" # macOS
  elif command -v xclip &>/dev/null; then
    xclip -selection clipboard < "$1" # Linux
  else
    echo "🟡 Could not find a clipboard command (pbcopy, xclip). Skipping copy." >&2
    echo "You can find the output in: $1"
    return
  fi
  echo "✅ Project structure copied to clipboard!"
}


# --- Script Execution ---

# Ensure 'tree' is installed
ensure_command tree

# Create a secure temporary file that will be removed on script exit
TEMP_FILE=$(mktemp)
trap 'rm -f "$TEMP_FILE"' EXIT

# Build the ignore pattern string for the 'tree' command
IGNORE_STRING=$(IFS="|"; echo "${EXCLUDE_PATTERNS[*]}")

echo "🔍 Generating structure for: $PROJECT_DIR..."

# Generate the directory tree, excluding specified patterns
tree "$PROJECT_DIR" \
  --dirsfirst \
  -a \
  -L 4 \
  -I "$IGNORE_STRING" > "$TEMP_FILE"

# Copy the generated structure to the clipboard
copy_to_clipboard "$TEMP_FILE"

# Display a preview of the output
echo "📋 Preview:"
head -n 25 "$TEMP_FILE"