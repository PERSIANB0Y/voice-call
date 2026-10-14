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
