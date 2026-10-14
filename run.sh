#!/usr/bin/env bash
# VoiceChat — one-click setup + run for Linux / macOS
# Usage: ./run.sh [--http] [--port N]
#   --http    run without TLS (localhost only for mic/camera)
#   --port N  override the default port (8000 for HTTP, 8443 for HTTPS)

set -euo pipefail

# ---------- colors ----------
if [ -t 1 ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'
  GRN=$'\033[32m'; YEL=$'\033[33m'; BLU=$'\033[34m'; CYA=$'\033[36m'
  RST=$'\033[0m'
else
  BOLD=""; DIM=""; RED=""; GRN=""; YEL=""; BLU=""; CYA=""; RST=""
fi

# ---------- args ----------
USE_HTTP=0
PORT_OVERRIDE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --http)  USE_HTTP=1; shift ;;
    --port)  PORT_OVERRIDE="$2"; shift 2 ;;
    -h|--help)
      cat <<EOF
VoiceChat launcher

Usage:
  ./run.sh              Start with HTTPS on port 8443 (recommended)
  ./run.sh --http       Start with HTTP on port 8000 (localhost only)
  ./run.sh --port 9000  Use a custom port

The first run creates venv/, installs dependencies, and (for HTTPS)
generates a self-signed certificate with make_cert.py.
EOF
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")"

printf '\n%s==========================================%s\n' "$CYA$BOLD" "$RST"
printf '%s   VoiceChat — Setup & Run%s\n' "$CYA$BOLD" "$RST"
printf '%s==========================================%s\n\n' "$CYA$BOLD" "$RST"

# ---------- 1. find python ----------
PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    # Must be Python 3.10+
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
      PY="$candidate"
      break
    fi
  fi
done

if [ -z "$PY" ]; then
  printf '%s[X]%s Python 3.10+ not found.\n' "$RED$BOLD" "$RST"
  echo    "    Install it with your package manager, e.g.:"
  echo    "      Ubuntu/Debian : sudo apt install python3 python3-venv python3-pip"
  echo    "      Fedora        : sudo dnf install python3 python3-pip"
  echo    "      Arch          : sudo pacman -S python python-pip"
  echo    "      macOS         : brew install python@3.12"
  exit 1
fi

printf '%s[1/6]%s Python: %s%s%s (%s)\n' \
  "$GRN$BOLD" "$RST" "$BOLD" "$PY" "$RST" "$("$PY" --version 2>&1)"

# ---------- 2. venv ----------
if [ -x "venv/bin/python" ]; then
  printf '%s[2/6]%s venv already exists — skipping\n' "$GRN$BOLD" "$RST"
else
  printf '%s[2/6]%s Creating venv…\n' "$GRN$BOLD" "$RST"
  # Some distros need python3-venv installed separately
  if ! "$PY" -m venv venv 2>/dev/null; then
    printf '%s[X]%s venv creation failed.\n' "$RED$BOLD" "$RST"
    echo    "    On Debian/Ubuntu, install the venv module:"
    echo    "      sudo apt install python3-venv"
    echo    "    On Fedora:"
    echo    "      sudo dnf install python3-virtualenv"
    exit 1
  fi
fi

VPY="$PWD/venv/bin/python"
if [ ! -x "$VPY" ]; then
  printf '%s[X]%s venv python missing at %s\n' "$RED$BOLD" "$RST" "$VPY"
  exit 1
fi

# ---------- 3. pip upgrade ----------
printf '%s[3/6]%s Upgrading pip…\n' "$GRN$BOLD" "$RST"
"$VPY" -m pip install --upgrade pip --quiet --disable-pip-version-check \
  || printf '%s[!]%s pip upgrade failed — continuing\n' "$YEL$BOLD" "$RST"

# ---------- 4. requirements ----------
if [ ! -f requirements.txt ]; then
  printf '%s[!]%s requirements.txt missing — writing default\n' "$YEL$BOLD" "$RST"
  cat > requirements.txt <<'REQ'
fastapi==0.115.6
uvicorn==0.34.0
websockets==14.1
python-multipart==0.0.20
cryptography==44.0.0
REQ
fi

printf '%s[4/6]%s Installing dependencies…\n' "$GRN$BOLD" "$RST"
if ! "$VPY" -m pip install -r requirements.txt --quiet --disable-pip-version-check; then
  printf '%s[X]%s Dependency installation failed.\n' "$RED$BOLD" "$RST"
  echo    "    Run it manually to see the full error:"
  echo    "      venv/bin/python -m pip install -r requirements.txt"
  exit 1
fi

# ---------- 5. certs ----------
WANT_HTTPS=1
[ "$USE_HTTP" = "1" ] && WANT_HTTPS=0

if [ "$WANT_HTTPS" = "1" ]; then
  if [ -f cert.pem ] && [ -f key.pem ]; then
    printf '%s[5/6]%s TLS certs already exist — skipping\n' "$GRN$BOLD" "$RST"
  elif [ -f make_cert.py ]; then
    printf '%s[5/6]%s Generating self-signed TLS certificate…\n' "$GRN$BOLD" "$RST"
    if ! "$VPY" make_cert.py; then
      printf '%s[!]%s Cert generation failed — falling back to HTTP\n' "$YEL$BOLD" "$RST"
      WANT_HTTPS=0
    fi
  else
    printf '%s[!]%s make_cert.py not found — falling back to HTTP\n' "$YEL$BOLD" "$RST"
    WANT_HTTPS=0
  fi
else
  printf '%s[5/6]%s HTTP mode requested — no certs needed\n' "$GRN$BOLD" "$RST"
fi

# ---------- detect LAN IP (best effort) ----------
LAN_IP=""
if command -v ip >/dev/null 2>&1; then
  LAN_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' | head -n1)
fi
if [ -z "$LAN_IP" ] && command -v ifconfig >/dev/null 2>&1; then
  LAN_IP=$(ifconfig 2>/dev/null | awk '/inet /&&!/127\.0\.0\.1/{print $2; exit}')
fi

# ---------- 6. run ----------
if [ "$WANT_HTTPS" = "1" ]; then
  PORT="${PORT_OVERRIDE:-8443}"
  RUN_ARGS=(server.py --port "$PORT" --ssl-keyfile key.pem --ssl-certfile cert.pem)
  SCHEME="https"
else
  PORT="${PORT_OVERRIDE:-8000}"
  RUN_ARGS=(server.py --port "$PORT")
  SCHEME="http"
fi

printf '\n%s==========================================%s\n' "$CYA$BOLD" "$RST"
printf '%s   Starting server…%s\n' "$CYA$BOLD" "$RST"
printf '%s==========================================%s\n\n' "$CYA$BOLD" "$RST"

printf '   Mode       : %s%s%s\n' "$BOLD" "${SCHEME^^}" "$RST"
printf '   URL        : %s%s://localhost:%s%s\n' "$BOLD" "$SCHEME" "$PORT" "$RST"
[ -n "$LAN_IP" ] && \
  printf '   LAN        : %s%s://%s:%s%s\n' "$BOLD" "$SCHEME" "$LAN_IP" "$PORT" "$RST"
[ "$SCHEME" = "http" ] && \
  printf '   %sNote: mic/cam need https:// or http://localhost%s\n' "$DIM" "$RST"
printf '\n   Press %sCtrl+C%s to stop.\n\n' "$BOLD" "$RST"

# Trap Ctrl+C so the "Server stopped" line prints cleanly
trap 'printf "\n%sServer stopped.%s\n" "$YEL$BOLD" "$RST"; exit 0' INT TERM

exec "$VPY" "${RUN_ARGS[@]}"