#!/usr/bin/env bash
# install_python3.11.sh
# Build and install Python 3.11.0 from source.
# Usage: sudo ./scripts/install_python3.11.sh

set -euo pipefail
IFS=$'\n\t'

VERSION="3.11.0"
TARBALL="Python-${VERSION}.tgz"
SRCDIR="Python-${VERSION}"
URL="https://www.python.org/ftp/python/${VERSION}/${TARBALL}"
PREFIX="/usr/local/python311"
TMPDIR=""  # will be set by mktemp
SUDO_CMD=""

log() { printf "[%s] %s\n" "$(date +'%Y-%m-%d %H:%M:%S')" "$*"; }
err() { log "ERROR: $*"; }
info() { log "INFO: $*"; }

cleanup() {
  if [[ -n "$TMPDIR" && -d "$TMPDIR" ]]; then
    info "Cleaning up temporary directory: $TMPDIR"
    rm -rf "$TMPDIR" || true
  fi
}
trap cleanup EXIT

check_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    return 1
  fi
  return 0
}

require_commands=("gcc" "make" "tar" "patch" "xz" "perl")

suggest_packages() {
  info "Missing system packages may be required to build Python. Suggested packages by distro:"
  cat <<'EOF'
- Debian/Ubuntu: build-essential libssl-dev zlib1g-dev libncurses5-dev libsqlite3-dev libreadline-dev libtk8.6-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev liblzma-dev uuid-dev
- RHEL/CentOS/Fedora: gcc openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel sqlite-devel xz
EOF
}

ensure_sudo() {
  if [[ "$EUID" -ne 0 ]]; then
    if check_command sudo; then
      SUDO_CMD=sudo
      info "Not running as root. Will use sudo for privileged operations."
    else
      err "This script needs to write to $PREFIX but 'sudo' is not available. Run as root or install sudo."
      exit 1
    fi
  else
    SUDO_CMD=""
  fi
}

main() {
  info "Starting build for Python $VERSION"

  ensure_sudo

  TMPDIR=$(mktemp -d /tmp/python-build-XXXXXX)
  info "Created temporary working directory: $TMPDIR"

  cd "$TMPDIR"

  # Download
  if check_command curl; then
    info "Downloading $TARBALL with curl from $URL"
    if ! curl -fSL "$URL" -o "$TARBALL"; then
      err "Download failed using curl"
      exit 2
    fi
  elif check_command wget; then
    info "Downloading $TARBALL with wget from $URL"
    if ! wget -q "$URL" -O "$TARBALL"; then
      err "Download failed using wget"
      exit 2
    fi
  else
    err "Neither curl nor wget found. Install one and re-run."
    exit 2
  fi
  info "Download completed: $TARBALL (size=$(stat -c%s "$TARBALL") bytes)"

  # Extract
  info "Extracting $TARBALL"
  if ! tar -xzf "$TARBALL"; then
    err "Extraction failed"
    exit 3
  fi
  info "Extraction completed"

  cd "$SRCDIR"

  # Show required packages check
  local missing=()
  for cmd in "$@"; do :; done
  for c in "${require_commands[@]}"; do
    if ! check_command "$c"; then
      missing+=("$c")
    fi
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    err "The following tools are missing: ${missing[*]}"
    suggest_packages
    info "You may still continue, but the build is likely to fail if development libraries are missing."
  else
    info "All basic build tools appear to be present"
  fi

  # Configure
  info "Configuring build with --enable-optimizations --prefix=$PREFIX"
  if ! ./configure --enable-optimizations --prefix="$PREFIX"; then
    err "Configure step failed"
    exit 4
  fi
  info "Configure completed"

  # Build
  NPROCS=1
  if check_command nproc; then
    NPROCS=$(nproc)
  elif check_command getconf; then
    NPROCS=$(getconf _NPROCESSORS_ONLN || echo 1)
  fi
  info "Starting build: make -j$NPROCS"
  if ! make -j"$NPROCS"; then
    err "Build (make) failed"
    exit 5
  fi
  info "Build completed"

  # Altinstall
  info "Installing to $PREFIX with 'make altinstall' (this will install python3.11 binary as python3.11 and avoid replacing system python)"
  if ! $SUDO_CMD make altinstall; then
    err "make altinstall failed"
    exit 6
  fi
  info "Installation completed"

  # Verify
  local PY_BIN="$PREFIX/bin/python3.11"
  if [[ ! -x "$PY_BIN" ]]; then
    err "Expected python binary not found at $PY_BIN"
    exit 7
  fi

  ACTUAL_VERSION=$($PY_BIN --version 2>&1 || true)
  info "Installed python reports: $ACTUAL_VERSION"

  if [[ "$ACTUAL_VERSION" == "Python $VERSION" ]]; then
    info "Verification PASSED: $PY_BIN --version == $ACTUAL_VERSION"
    cat <<EOF

SUCCESS: Python $VERSION has been built and installed to $PREFIX
- Binary: $PY_BIN

To use this Python in your shell add to PATH, e.g.:
  export PATH=$PREFIX/bin:\$PATH

Or create symlinks (optional/root):
  sudo ln -s $PY_BIN /usr/local/bin/python3.11

EOF
    exit 0
  else
    err "Verification FAILED: expected 'Python $VERSION' but got: $ACTUAL_VERSION"
    exit 8
  fi
}

# Run main with all args forwarded
main "$@"
