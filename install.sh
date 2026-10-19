#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/tc4dy/privmeta.git"
PKG_NAME="privmeta"
MIN_PY="3.9"

RED=$'\033[31m'
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
CYAN=$'\033[36m'
BOLD=$'\033[1m'
DIM=$'\033[90m'
RESET=$'\033[0m'

step() { printf '%s[>]%s %s\n' "$CYAN" "$RESET" "$1"; }
ok()   { printf '%s[+]%s %s\n' "$GREEN" "$RESET" "$1"; }
warn() { printf '%s[!]%s %s\n' "$YELLOW" "$RESET" "$1"; }
fail() { printf '%s[-]%s %s\n' "$RED" "$RESET" "$1" >&2; }

finish_fail() {
    fail "$1"
    exit 1
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

detect_python() {
    if command_exists python3; then
        printf 'python3'
        return 0
    fi
    if command_exists python; then
        printf 'python'
        return 0
    fi
    finish_fail "Python is not installed. Install Python ${MIN_PY}+ and run again."
}

python_ok() {
    local py="$1"
    "$py" -c "import sys; sys.exit(0 if sys.version_info >= (${MIN_PY//./,}) else 1)" >/dev/null 2>&1
}

detect_pip() {
    local py="$1"
    if "$py" -m pip --version >/dev/null 2>&1; then
        printf '%s -m pip' "$py"
        return 0
    fi
    finish_fail "pip is not available for ${py}. Install pip and run again."
}

is_termux() {
    [ -n "${PREFIX:-}" ] && [ -d "${PREFIX}/bin" ]
}

in_path() {
    case ":${PATH}:" in
        *:"$1":*) return 0 ;;
        *) return 1 ;;
    esac
}

step "PrivMeta installer"
printf '%srepo:%s %s\n\n' "$DIM" "$RESET" "$REPO"

PY_BIN="$(detect_python)"
step "python: ${PY_BIN}"

if ! python_ok "$PY_BIN"; then
    finish_fail "Python ${MIN_PY} or newer is required."
fi
PY_VERSION="$("$PY_BIN" -c 'import sys; print("{}.{}.{}".format(*sys.version_info[:3]))')"
ok "python version: ${PY_VERSION}"

PIP_CMD="$(detect_pip "$PY_BIN")"
step "pip: ${PIP_CMD}"

if is_termux; then
    step "detected Termux environment"
fi

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

step "fetching repository"
if command_exists git; then
    if ! git clone --depth 1 "$REPO" "${WORK_DIR}/${PKG_NAME}" >/dev/null 2>&1; then
        finish_fail "git clone failed. Check your network or the repository URL."
    fi
else
    warn "git is not installed, trying archive download"
    ARCHIVE="${WORK_DIR}/src.tar.gz"
    if ! curl -sSL "https://github.com/tc4dy/privmeta/archive/refs/heads/main.tar.gz" -o "$ARCHIVE"; then
        finish_fail "download failed. Install git or check your network."
    fi
    if ! tar -xzf "$ARCHIVE" -C "$WORK_DIR"; then
        finish_fail "extracting archive failed."
    fi
    mv "${WORK_DIR}/privmeta-main" "${WORK_DIR}/${PKG_NAME}" 2>/dev/null || true
fi
ok "source ready"

step "installing package"
cd "${WORK_DIR}/${PKG_NAME}"
if ! $PIP_CMD install --user --upgrade . >/tmp/privmeta-install.log 2>&1; then
    tail -n 30 /tmp/privmeta-install.log >&2 || true
    finish_fail "pip install failed. See log above."
fi
ok "package installed"

step "checking optional dependencies"
ask_optional() {
    local prompt="$1"
    local module="$2"
    local extra="$3"
    printf '%s[?]%s %s (y/N): ' "$CYAN" "$RESET" "$prompt"
    read -r reply || reply="n"
    case "$reply" in
        [yY]|[yY][eE][sS])
            if $PIP_CMD install --user "$module" >/dev/null 2>&1; then
                ok "installed ${extra}"
            else
                warn "could not install ${extra}, continuing without it"
            fi
            ;;
        *)
            printf '%s[>]%s skipping %s\n' "$DIM" "$RESET" "$extra"
            ;;
    esac
}

if ! $PY_BIN -c "import pypdf" >/dev/null 2>&1; then
    ask_optional "install PDF support (pypdf)" "pypdf" "pypdf"
fi

if ! $PY_BIN -c "import mutagen" >/dev/null 2>&1; then
    ask_optional "install audio support (mutagen)" "mutagen" "mutagen"
fi

if ! command_exists ffmpeg; then
    warn "ffmpeg is not installed. Video shredding will fail until you install it."
    if is_termux; then
        printf '%s[>]%s run: pkg install ffmpeg\n' "$DIM" "$RESET"
    fi
fi

step "verifying installation"
USER_BIN="${HOME}/.local/bin"
if ! in_path "$USER_BIN"; then
    warn "${USER_BIN} is not in PATH"
    SHELL_NAME="$(basename "${SHELL:-bash}")"
    case "$SHELL_NAME" in
        zsh)
            RC_FILE="${HOME}/.zshrc"
            ;;
        bash)
            RC_FILE="${HOME}/.bashrc"
            ;;
        *)
            RC_FILE="${HOME}/.profile"
            ;;
    esac
    printf '%s[?]%s add %s to PATH in %s? (y/N): ' "$CYAN" "$RESET" "$USER_BIN" "$RC_FILE"
    read -r reply || reply="n"
    case "$reply" in
        [yY]|[yY][eE][sS])
            printf '\nexport PATH="%s:$PATH"\n' "$USER_BIN" >> "$RC_FILE"
            ok "PATH updated in ${RC_FILE} (restart your shell)"
            ;;
        *)
            warn "add it manually: export PATH=\"${USER_BIN}:\$PATH\""
            ;;
    esac
fi

if command_exists privmeta; then
    ok "privmeta is available on PATH"
else
    warn "privmeta is not on PATH yet, try: ${USER_BIN}/privmeta"
fi

printf '\n'
ok "install finished"
printf '%s[>]%s run: %sprivmeta%s\n' "$CYAN" "$RESET" "$BOLD" "$RESET"