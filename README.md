# VoiceChat

A self-hosted WebRTC voice/video/screen-share room server with file sharing, sound pad, and admin controls. Single-file Python server, single-file HTML client — no build step, no dependencies beyond pip.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Voice & video** — peer-to-peer WebRTC mesh (up to 12 peers per room)
- **Screen share** — with Fast / Quality presets, works alongside camera
- **File sharing** — drag & drop, paste from clipboard, or browse; files stored server-side and served to the room
- **Sound pad** — 6 built-in ringtone clips so users without a mic can "talk"; rate-limited to 1/sec, 10/min
- **Chat** — merged into a chronological timeline with files and sounds
- **Voice visualizer** — live EQ bars + speaking glow on each tile
- **Admin mode** — random password printed at startup; mute or kick anyone
- **Themes** — accent colors, animations toggle, mic/camera device pickers
- **Layout** — drag-and-drop tiles, per-tile fullscreen, screen share auto-spotlights
- **Text/chat features** — persists until server restart; files persist on disk

---

## Quick Start

### One-click (Windows)

```bat
run.bat
