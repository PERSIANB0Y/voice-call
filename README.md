# VoiceChat

A self-hosted WebRTC voice, video, and screen-share server with file sharing, a sound pad, and admin controls. One Python file for the backend, one HTML file for the frontend. No build step, no npm, no framework churn.

Works on Windows, Linux, and macOS. Runs over HTTPS with an auto-generated self-signed certificate, so mic and camera work on any LAN — not just `localhost`.

---

## Features

- **Voice & video** — peer-to-peer WebRTC mesh, up to 12 peers per room
- **Screen sharing** — Fast or Quality presets, works alongside camera
- **File sharing** — drag & drop, paste from clipboard, or browse; files persist on disk and serve to the room
- **Sound pad** — six built-in ringtone clips for mic-less users, rate-limited server-side and client-side
- **Chat** — chronological timeline merging messages, files, and sound events
- **Voice visualizer** — live EQ bars and speaking glow per tile
- **Admin mode** — random password printed at server start; mute or kick anyone
- **Custom themes** — accent colors, animations toggle, mic/camera device pickers
- **Layout** — drag-and-drop tiles, per-tile fullscreen, screen share auto-spotlights
- **Zero config** — one script bootstraps venv, installs deps, generates certs, starts server

---

## Quick Start

### Windows

```bat
run.bat
