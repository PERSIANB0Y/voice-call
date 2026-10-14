<div align="center">

# VoiceChat

**Self-hosted voice, video, screen-share, and file-transfer for small groups.**

One Python backend. One HTML frontend. No build step. No cloud. No accounts.

[Features](#features) · [Quick Start](#quick-start) · [Usage](#usage) · [Configuration](#configuration) · [Troubleshooting](#troubleshooting)

</div>

---

## Why VoiceChat

Most voice-chat solutions require either a cloud account (Discord, Zoom, Meet) or a heavy self-hosted stack (Jitsi, Mumble + plugins, Matrix). VoiceChat is different:

- **One file for the server** — a single `server.py` runs WebRTC signaling, static hosting, file storage, and admin controls.
- **One file for the client** — `static/index.html` contains all HTML, CSS, and JavaScript. No bundler, no npm, no build.
- **Runs on anything** — Windows, Linux, macOS. Any machine that can run Python 3.10.
- **HTTPS by default** — auto-generates a self-signed cert so mic and camera work on LAN IPs, not just `localhost`.
- **No external services** — no TURN, no SFU, no database, no Redis. Peers connect directly.

Ideal for LAN parties, virtual LANs (ZeroTier, Tailscale, Hamachi, PacketRaft), small team standups, gaming groups, and anyone who wants a private voice room without handing data to a third party.

---

## Features

| Category | What's included |
|---|---|
| **Voice** | Peer-to-peer Opus, adjustable bitrate (6–128 kbps), noise suppression, echo cancellation, forward error correction, silence suppression (DTX), push-to-talk |
| **Video** | Camera at up to 1080p60, adaptive degradation preference, H.264/VP9 preference, mirror-own-camera toggle |
| **Screen share** | Fast (720p30, 1.5 Mbps) or Quality (1080p60, 8 Mbps) presets, switchable mid-call, works alongside camera |
| **Files** | Unlimited size, streamed to disk in 1 MB chunks, drag & drop, clipboard paste, inline image/video/audio previews, download button, cancel mid-upload |
| **Chat** | Merged timeline of messages, files, and sound events, sorted by time |
| **Sound pad** | 12 built-in tones + unlimited custom uploads, rate-limited 1/s and 10/min, admin bypass mode |
| **Admin** | Random password printed at startup, mute / unmute / kick participants, rate-limit bypass, custom sound upload |
| **Layout** | Google-Meet-style grid, drag-and-drop tile reordering with bounce animation, per-tile fullscreen, screen share auto-spotlights |
| **Appearance** | Custom accent colors, animation toggle, voice visualizer bars, per-user settings persist in localStorage |
| **Devices** | Explicit microphone and camera device pickers, remembered between sessions |
| **Mobile** | Responsive layout, full-width scrollable bottom bar, popups become centered sheets, iOS safe-area support |

---

## Requirements

- **Python 3.10 or newer** (3.12 and 3.13 tested)
- A modern browser: Chrome 90+, Firefox 88+, Safari 15+, Edge 90+
- Optional but recommended: a **LAN, VPN, or virtual LAN** (ZeroTier, Tailscale, Hamachi, PacketRaft) so peers can reach each other directly

---

## Quick Start

Pick your platform. Both scripts do exactly the same thing:

1. Find a Python 3.10+ interpreter
2. Create `venv/`
3. Install the five dependencies
4. Generate a self-signed TLS certificate
5. Start the server on **https://localhost:8443**

First run takes ~30 seconds. Every run after that is ~2 seconds.

### Windows

```bat
run.bat
```

Double-click `run.bat`, or run it from a Command Prompt or PowerShell window.

### Linux / macOS

```bash
chmod +x run.sh
./run.sh
```

The `chmod` is one-time.

Once running, open **https://localhost:8443** in your browser.

---

## Launcher Options

Both `run.bat` and `run.sh` accept the same flags.

| Flag | Short | Effect |
|---|---|---|
| *(none)* | | **HTTPS on port 8443** — recommended, mic/cam work on LAN |
| `--http` | | **HTTP on port 8000** — `localhost` only, mic/cam disabled on LAN IPs |
| `--port N` | | Override the default port |
| `--help` | `-h` | Show usage |

### Examples

```bat
:: Windows
run.bat                         ::  https://localhost:8443
run.bat --http                  ::  http://localhost:8000
run.bat --port 9000             ::  https://localhost:9000
run.bat --http --port 8080      ::  http://localhost:8080
```

```bash
# Linux / macOS
./run.sh                        #   https://localhost:8443
./run.sh --http                 #   http://localhost:8000
./run.sh --port 9000            #   https://localhost:9000
./run.sh --http --port 8080     #   http://localhost:8080
```

---

## Usage

### Joining a room

1. Open the URL the server prints (or the one you shared with your friends)
2. Enter your **name** and a **room code** (any string — everyone with the same code lands in the same room)
3. Click **Join room**
4. Grant microphone and camera permission when your browser asks

If the browser doesn't prompt, or if the mic/cam stays off, you're probably on an **insecure origin** (see [HTTPS and secure contexts](#https-and-secure-contexts)).

### In-call controls

The floating bar at the bottom contains everything. On phones it scrolls horizontally.

| Button | What it does |
|---|---|
| **🎤 Microphone** | Toggle mic on/off. The chevron next to it opens a popup with device, bitrate, DSP toggles, push-to-talk |
| **📷 Camera** | Toggle camera. Chevron opens device, resolution, framerate, mirror |
| **🖥 Screen** | Start / stop screen sharing (uses the current quality preset) |
| **🔔 Sounds** | Open the sound pad — 12 built-in tones plus any custom sounds uploaded |
| **💬 Chat** | Open the chat / timeline panel |
| **📎 Files** | Open the file panel with drop zone and file grid |
| **⚙ Settings** | Open the settings sheet |
| **✕ Leave** | Disconnect and reload |

### Side panel tabs

- **Chat** — a chronological timeline of messages, uploaded files, and sound events. Image and video files render inline; click an image to open the lightbox.
- **Files** — a grid of every file shared in the room, with download buttons and image thumbnails.
- **Sounds** — the full sound pad.
- **Admin** — password field and, once unlocked, mute / kick / bypass controls.

### Uploading files

Three ways:

1. **Drag & drop** anywhere on the window — the Files panel opens automatically
2. **Paste** an image or file from the clipboard (**Ctrl+V** / **Cmd+V**)
3. Click the drop zone to browse

Files upload in the background. A progress bar shows bytes transferred, current speed, and estimated time remaining. Click the **✕** on any row to cancel.

### Sound pad

Twelve built-in tones: **Yes**, **No**, **I'm here**, **Come chat**, **Hello**, **Wait**, **Stop**, **Clap**, **Success**, **Error**, **Ping**, **Alert**. All synthesized with the Web Audio API — no audio files to ship.

Custom sounds can be added two ways:

1. Drop `.mp3` / `.ogg` / `.wav` / `.m4a` / `.webm` / `.opus` / `.flac` files into `static/sounds/` and restart the server
2. Log in as admin, open the **Sounds** tab, and use the **Upload sound** button

Rate limiting: **1 sound per second** and **10 sounds per rolling 60 seconds** per peer. Admins can bypass with the toggle.

### Admin mode

Every time the server starts it prints a **new random six-character password** to the console:

```
============================================================
  VoiceChat server starting
============================================================
  URL            : https://0.0.0.0:8443
  Uploads folder : /home/user/voicechat/files
  Sounds folder  : /home/user/voicechat/static/sounds

  *** ADMIN PASSWORD: A3K7QX ***

  Share this with whoever should be able to mute/kick.
  It is different every time the server restarts.
============================================================
```

Enter it under **Admin** to unlock:

- **Mute / unmute** any participant — server-enforced, they can't unmute themselves
- **Kick** any participant — closes their WebSocket
- **Bypass rate limit** — spam sound pad with no 1/s or 10/min cap
- **Upload sounds** — add custom audio to everyone's pad

Admin status is per-session. Multiple people can be admin simultaneously. Restart the server to rotate the password.

---

## HTTPS and Secure Contexts

Browsers only expose `navigator.mediaDevices` (microphone, camera) on a **secure context** — that means `https://` or `http://localhost`. Anything else, including `http://192.168.1.5`, silently disables media access.

`make_cert.py` (called automatically by both launchers) generates a self-signed certificate covering `localhost`, `127.0.0.1`, your hostname, and your LAN IP. On first visit your browser shows a warning — click **Advanced → Proceed**.

### Editing the certificate

Before running `make_cert.py` the first time, open it and set `LAN_IP` to your machine's LAN address:

| Platform | How to find it |
|---|---|
| Windows | `ipconfig` — look for **IPv4 Address** |
| Linux | `ip a` or `hostname -I` — look for `inet` |
| macOS | `ifconfig \| grep "inet "` — non-loopback entry |

If you change networks later, delete `cert.pem` and `key.pem` and rerun the launcher.

### Trusting the certificate (optional)

To remove the browser warning permanently, install `cert.pem` as a Trusted Root CA.

| Platform | Command |
|---|---|
| **Windows** | Double-click `cert.pem` → **Install Certificate** → **Local Machine** → **Trusted Root Certification Authorities** |
| **Ubuntu / Debian** | `sudo cp cert.pem /usr/local/share/ca-certificates/voicechat.crt && sudo update-ca-certificates` |
| **Fedora / RHEL** | `sudo cp cert.pem /etc/pki/ca-trust/source/anchors/voicechat.pem && sudo update-ca-trust` |
| **Arch** | `sudo cp cert.pem /etc/ca-certificates/trust-source/anchors/voicechat.crt && sudo trust extract-compat` |
| **macOS** | `sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain cert.pem` |

Firefox uses its own trust store — add `cert.pem` manually under **Settings → Privacy & Security → Certificates → View Certificates → Authorities → Import**.

---

## Manual Setup

If you prefer not to use the launchers.

### Windows

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

REM Optional — edit LAN_IP in make_cert.py first
python make_cert.py

REM HTTPS (recommended)
python server.py --port 8443 --ssl-keyfile key.pem --ssl-certfile cert.pem

REM HTTP (localhost only)
python server.py
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Optional — edit LAN_IP in make_cert.py first
python make_cert.py

# HTTPS (recommended)
python server.py --port 8443 --ssl-keyfile key.pem --ssl-certfile cert.pem

# HTTP (localhost only)
python server.py
```

### Linux system prerequisites

Minimal Linux installs often lack the `venv` module or `pip`. If `run.sh` fails at the venv step:

| Distro | Install command |
|---|---|
| Ubuntu / Debian | `sudo apt install python3 python3-venv python3-pip` |
| Fedora / RHEL | `sudo dnf install python3 python3-pip python3-virtualenv` |
| Arch / Manjaro | `sudo pacman -S python python-pip` |
| openSUSE | `sudo zypper install python3 python3-pip python3-virtualenv` |
| macOS | `brew install python@3.12` |

---

## Project Layout

```
voicechat/
├── run.bat                # Windows one-click launcher
├── run.sh                 # Linux / macOS one-click launcher
├── server.py              # FastAPI signaling + static + uploads
├── make_cert.py           # Self-signed TLS certificate generator
├── requirements.txt
├── cert.pem               # Generated on first run
├── key.pem                # Generated on first run
├── favicon.ico            # Optional
├── files/                 # Uploaded files (auto-created)
└── static/
    ├── index.html         # Entire client: HTML + CSS + JS
    └── sounds/            # Custom sound clips (auto-created)
```

---

## Configuration

### Server flags

| Flag | Default | Description |
|---|---|---|
| `--host` | `0.0.0.0` | Bind address. Use `::` for dual-stack IPv4 + IPv6. |
| `--port` | `8000` | Port number |
| `--ssl-keyfile` | — | Path to `key.pem` |
| `--ssl-certfile` | — | Path to `cert.pem` |
| `--reload` | off | Auto-restart on file changes (dev only) |

### Server tunables (`server.py`)

```python
MAX_PEERS         = 12                    # room capacity
MAX_SOUND_BYTES   = 5 * 1024 * 1024       # 5 MB per sound upload
SOUND_MIN_GAP     = 1.0                   # seconds between sounds per peer
SOUND_MAX_PER_MIN = 10                    # rolling 60s window cap
HELLO_TIMEOUT     = 15.0                  # seconds to send the initial hello
```

File uploads have **no size limit** — they stream to disk in 1 MB chunks.

### Client-side defaults (`static/index.html`)

```js
const settings = {
  animations:  true,     // master animation toggle
  viz:         true,     // voice visualizer bars
  mirror:      true,     // mirror own camera
  selfTile:    true,     // show my own tile in the grid
  ns:          false,    // noise suppression (off by default)
  ec:          false,    // echo cancellation (off by default)
  ptt:         false,    // push-to-talk
  micOnJoin:   true,     // request mic at join
  fec:         false,    // forward error correction
  dtx:         false,    // silence suppression
};

const audioSettings = { bitrateKbps: 32 };  // 6–128 kbps Opus bitrate
```

Change these if you want different starting states for new users. Existing users keep their localStorage values.

---

## How It Works

### Signaling

Each client opens a WebSocket at `wss://host/ws/<room>`. The server assigns a random peer ID, returns the current roster, and relays SDP offers/answers and ICE candidates between peers. Chat, sound events, file notifications, and state changes ride the same socket.

Server state is in-memory only. Rooms self-delete when the last peer leaves. No database, no session files.

### WebRTC mesh

Every peer connects directly to every other peer — full mesh. No SFU, no relay. Fine for ≤ 8 peers on a LAN; beyond that an SFU like mediasoup or LiveKit pays off.

**Track handling:** at peer creation, a placeholder track (a 320×180 animated canvas for video, a silent Web Audio oscillator for audio) is attached with `pc.addTrack()`. This bakes a real msid into the initial SDP so the remote's `ontrack` event fires reliably. When a user enables mic, camera, or screen share, the sender swaps to the real track with `replaceTrack()` — no renegotiation, no reconnect. On stop, it swaps to the placeholder **first**, then stops the real track, so the receiver renders black instead of a frozen frame.

### Opus tuning

Before the initial offer is sent, `tuneOpusSdp()` rewrites the Opus fmtp line to inject:

- `maxaveragebitrate` — the user's chosen bitrate (6–128 kbps)
- `useinbandfec=1` — forward error correction for packet loss recovery
- `usedtx=1` — silence suppression (discontinuous transmission)
- `stereo=0`, `sprop-stereo=0` — forces mono, halves bandwidth
- `ptime=20` — 20 ms packet time

Changes mid-call update `setParameters()` without SDP renegotiation.

### Video quality presets

Two modes, switchable live during a call:

| Preset | Camera | Screen | Bitrate | Degradation |
|---|---|---|---|---|
| **Fast** | 720p30 | 720p30 | 1.2 / 1.5 Mbps | `maintain-framerate` |
| **Quality** | 720p30 | 1080p60 | 4 / 8 Mbps | `maintain-resolution` |

Codec preference is H.264 → VP9 → everything else. H.264 is hardware-accelerated on virtually all modern devices, keeping CPU usage low.

---

## Firewall

If a remote machine can't reach the server but `localhost` works, it's a firewall issue.

### Windows

Run as Administrator:

```powershell
New-NetFirewallRule -DisplayName "VoiceChat" `
  -Direction Inbound -Protocol TCP -LocalPort 8443 -Action Allow -Profile Any
```

`-Profile Any` covers Domain, Private, and Public networks.

### Linux

```bash
# ufw (Ubuntu / Debian)
sudo ufw allow 8443/tcp

# firewalld (Fedora / RHEL)
sudo firewall-cmd --add-port=8443/tcp --permanent
sudo firewall-cmd --reload

# iptables (manual)
sudo iptables -A INPUT -p tcp --dport 8443 -j ACCEPT
```

`localhost` and `127.0.0.1` always work regardless.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ERR_EMPTY_RESPONSE` | Typing `http://` on the HTTPS port | Use `https://` |
| `localhost` fails, LAN IP works | IPv6-only resolution on Windows | Use `127.0.0.1` or add `--host ::` |
| Mic / cam not available | Insecure origin | Serve over `https://` or use `http://localhost` |
| Remote machine can't reach server | Firewall | See [Firewall](#firewall) |
| Black tile for a peer | NAT with no TURN | Add a coturn server to `ICE_SERVERS` in `index.html` |
| Screen share black on remote | Old client | Reload both browsers — current build swaps to placeholder before stop |
| Cert warning on every visit | Untrusted self-signed cert | See [Trusting the certificate](#trusting-the-certificate-optional) |
| `python3-venv` not found (Linux) | Missing system package | See [Linux prerequisites](#linux-system-prerequisites) |
| `Permission denied` running `run.sh` | Missing executable bit | `chmod +x run.sh` |
| Sound pad not working | Rate limit hit | Wait 1 second; check the pad's status bar |

### Debugging WebRTC

Open DevTools (**F12**) on both machines and watch the console:

- `[ontrack] audio from <id>` — remote audio arrived ✅
- `[ontrack] video from <id>` — remote video arrived ✅
- `[pc] <id> connected` — peer connection established ✅

If `[ontrack] video` never appears, the SDP isn't carrying a video msid. Check `chrome://webrtc-internals` for `framesReceived` — if it's 0, the sender isn't producing frames.

---

## Scaling

The current design is a **full mesh** — every peer connects to every other peer. Bandwidth and encoding CPU grow as O(n²).

| Peers | Feasibility |
|---|---|
| ≤ 6 on a LAN | Fine, even on modest hardware |
| 6–12 | OK if most are audio-only and the host is decent |
| 12+ | Switch to an SFU (mediasoup, Janus, LiveKit) |

The server itself is stateless apart from in-memory room membership. Horizontal scaling requires sticky routing per room or a shared pub/sub for signaling.

---

## Security Notes

- **No authentication on rooms** — anyone who knows the room code can join. Use unguessable room codes for private conversations.
- **Admin password is rotated every restart** — you must share the new one each time.
- **Files are unlisted but not authenticated** — URLs contain UUIDs, but anyone with the URL can download.
- **No TLS certificate authority** — the cert is self-signed. If you need a real cert, front the server with nginx / Caddy and use Let's Encrypt.
- **No end-to-end encryption beyond WebRTC's default DTLS-SRTP** — traffic is encrypted in transit between peers, but the signaling server sees SDP and metadata.

For production deployment on the public internet, put the server behind a reverse proxy with a real certificate, restrict upload size in nginx, and consider adding authentication.

---

## License

MIT

---

<div align="center">

Built with [FastAPI](https://fastapi.tiangolo.com/) · [Uvicorn](https://www.uvicorn.org/) · WebRTC · Web Audio API

</div>
