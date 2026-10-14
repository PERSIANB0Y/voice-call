"""
server.py — FastAPI signaling + static + file store for a WebRTC voice/video room.

Admin password is randomly generated on each startup and printed to the console.

Custom sounds: drop .mp3/.ogg/.wav/.m4a files into static/sounds/ OR upload
them from the admin panel. They're auto-discovered and served alongside the
built-in synthesized clips.

Uploads are streamed to disk in 1 MB chunks — no size limit.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import mimetypes
import secrets
import string
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("voicechat")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"
FAVICON_FILE = BASE_DIR / "favicon.ico"
FILES_DIR = BASE_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)
SOUNDS_DIR = STATIC_DIR / "sounds"
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_EXTS = {".mp3", ".ogg", ".wav", ".m4a", ".webm", ".opus", ".flac"}

# --- Tunables --------------------------------------------------------------
MAX_PEERS = 12
MAX_MSG_BYTES = 64 * 1024
MAX_SOUND_BYTES = 5 * 1024 * 1024
HELLO_TIMEOUT = 15.0
SEP = (",", ":")

SOUND_MIN_GAP = 1.0
SOUND_MAX_PER_MIN = 10

ADMIN_PASSWORD = "".join(
    secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)
)

BUILTIN_SOUNDS = {
    "yes", "no", "here", "come", "hello", "wait",
    "stop", "clap", "success", "error", "ping", "alert",
}


# ---------------------------------------------------------------------------
class Peer:
    __slots__ = ("id", "name", "ws", "muted", "video", "screen",
                 "is_admin", "muted_by_admin", "sound_times")

    def __init__(self, pid: str, name: str, ws: WebSocket) -> None:
        self.id = pid
        self.name = name
        self.ws = ws
        self.muted = False
        self.video = False
        self.screen = False
        self.is_admin = False
        self.muted_by_admin = False
        self.sound_times: deque[float] = deque(maxlen=64)

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "muted": self.muted,
            "video": self.video, "screen": self.screen,
            "isAdmin": self.is_admin, "mutedByAdmin": self.muted_by_admin,
        }


class Room:
    __slots__ = ("id", "peers", "lock")

    def __init__(self, rid: str) -> None:
        self.id = rid
        self.peers: dict[str, Peer] = {}
        self.lock = asyncio.Lock()

    async def send_to(self, pid: str, msg: dict[str, Any]) -> bool:
        p = self.peers.get(pid)
        if p is None:
            return False
        try:
            await p.ws.send_text(json.dumps(msg, separators=SEP))
            return True
        except Exception:
            self.peers.pop(pid, None)
            return False

    async def broadcast(self, msg: dict[str, Any], exclude: str | None = None) -> None:
        targets = [p for pid, p in self.peers.items() if pid != exclude]
        if not targets:
            return
        data = json.dumps(msg, separators=SEP)
        results = await asyncio.gather(
            *(p.ws.send_text(data) for p in targets), return_exceptions=True
        )
        for p, r in zip(targets, results):
            if isinstance(r, BaseException):
                self.peers.pop(p.id, None)


ROOMS: dict[str, Room] = {}
ROOMS_LOCK = asyncio.Lock()


# ---------------------------------------------------------------------------
app = FastAPI(title="VoiceChat", docs_url=None, redoc_url=None, openapi_url=None)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/files", StaticFiles(directory=str(FILES_DIR)), name="files")


@app.get("/")
async def index() -> FileResponse:
    if not INDEX_FILE.is_file():
        return JSONResponse({"error": f"missing {INDEX_FILE}"}, status_code=500)
    return FileResponse(INDEX_FILE, media_type="text/html",
                        headers={"Cache-Control": "no-cache"})


@app.get("/favicon.ico")
async def favicon():
    if FAVICON_FILE.is_file():
        return FileResponse(FAVICON_FILE, media_type="image/x-icon",
                            headers={"Cache-Control": "public, max-age=86400"})
    return JSONResponse(status_code=204, content=None)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({
        "ok": True,
        "rooms": len(ROOMS),
        "peers": sum(len(r.peers) for r in ROOMS.values()),
    })


# ---------------------------------------------------------------------------
# Custom sounds
# ---------------------------------------------------------------------------
def scan_custom_sounds() -> list[dict[str, str]]:
    out = []
    if not SOUNDS_DIR.is_dir():
        return out
    for f in sorted(SOUNDS_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in AUDIO_EXTS:
            nice = f.stem.replace("_", " ").replace("-", " ").strip()
            nice = " ".join(w.capitalize() for w in nice.split()) or f.stem
            out.append({
                "id": f"file:{f.stem}",
                "name": nice[:40],
                "url": f"/static/sounds/{f.name}",
            })
    return out


@app.get("/sounds")
async def list_sounds() -> JSONResponse:
    return JSONResponse({
        "custom": scan_custom_sounds(),
        "builtin": sorted(BUILTIN_SOUNDS),
    })


@app.post("/sounds/upload")
async def upload_sound(password: str = Form(...), file: UploadFile = File(...)):
    if password != ADMIN_PASSWORD:
        return JSONResponse({"error": "unauthorized"}, status_code=403)
    orig = (file.filename or "sound").replace("\\", "/").split("/")[-1][:120]
    ext = Path(orig).suffix.lower()
    if ext not in AUDIO_EXTS:
        return JSONResponse({"error": "unsupported format"}, status_code=400)
    stem = Path(orig).stem
    safe = "".join(c for c in stem if c.isalnum() or c in "._- ")[:60].strip() or "sound"
    dest = SOUNDS_DIR / f"{safe}{ext}"
    i = 1
    while dest.exists():
        dest = SOUNDS_DIR / f"{safe}_{i}{ext}"
        i += 1
    size = 0
    try:
        with dest.open("wb") as f:
            while True:
                chunk = await file.read(1 << 18)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_SOUND_BYTES:
                    f.close()
                    dest.unlink(missing_ok=True)
                    return JSONResponse({"error": "sound too large (max 5 MB)"}, status_code=413)
                f.write(chunk)
    except Exception as e:
        dest.unlink(missing_ok=True)
        log.exception("sound upload failed")
        return JSONResponse({"error": str(e)}, status_code=500)
    log.info("custom sound uploaded: %s (%d bytes)", dest.name, size)
    return {"ok": True, "id": f"file:{dest.stem}", "name": dest.stem,
            "url": f"/static/sounds/{dest.name}"}


# ---------------------------------------------------------------------------
# File uploads — no size limit, streamed to disk in 1 MB chunks
# ---------------------------------------------------------------------------
@app.post("/upload/{room_id}")
async def upload(room_id: str, file: UploadFile = File(...)):
    room = ROOMS.get(room_id)
    if room is None:
        return JSONResponse({"error": "room not found"}, status_code=404)

    orig = (file.filename or "file").replace("\\", "/").split("/")[-1][:200] or "file"
    ext = Path(orig).suffix[:16]
    fid = uuid.uuid4().hex
    fname = f"{fid}{ext}"
    dest = FILES_DIR / fname

    size = 0
    try:
        with dest.open("wb") as f:
            while True:
                chunk = await file.read(1 << 20)  # 1 MB chunks
                if not chunk:
                    break
                size += len(chunk)
                f.write(chunk)
    except Exception as e:
        dest.unlink(missing_ok=True)
        log.exception("upload failed")
        return JSONResponse({"error": str(e)}, status_code=500)

    mime = file.content_type or mimetypes.guess_type(orig)[0] or "application/octet-stream"
    url = f"/files/{fname}"
    info = {"id": fid, "name": orig, "size": size, "mime": mime, "url": url,
            "uploaded": int(time.time() * 1000)}

    await room.broadcast({"t": "file", **info})
    log.info("file room=%s name=%s size=%d", room_id, orig, size)
    return info


# ---------------------------------------------------------------------------
def sound_allowed(peer: Peer) -> bool:
    now = time.time()
    while peer.sound_times and now - peer.sound_times[0] > 60:
        peer.sound_times.popleft()
    if peer.sound_times and now - peer.sound_times[-1] < SOUND_MIN_GAP:
        return False
    if len(peer.sound_times) >= SOUND_MAX_PER_MIN:
        return False
    peer.sound_times.append(now)
    return True


# ---------------------------------------------------------------------------
async def handle_signal(room: Room, peer: Peer, msg: dict[str, Any]) -> None:
    t = msg.get("t")

    if t in ("offer", "answer", "ice"):
        to = msg.get("to")
        if not isinstance(to, str):
            return
        out: dict[str, Any] = {"t": t, "from": peer.id}
        if t == "ice":
            out["c"] = msg.get("c")
        else:
            out["sdp"] = msg.get("sdp")
        await room.send_to(to, out)

    elif t == "state":
        peer.muted = bool(msg.get("muted"))
        peer.video = bool(msg.get("video"))
        peer.screen = bool(msg.get("screen"))
        if peer.muted_by_admin:
            peer.muted = True
        await room.broadcast(
            {"t": "peer-state", "id": peer.id,
             "muted": peer.muted, "video": peer.video, "screen": peer.screen},
            exclude=peer.id,
        )

    elif t == "chat":
        text = str(msg.get("text", ""))[:500].strip()
        if text:
            await room.broadcast(
                {"t": "chat", "from": peer.id, "name": peer.name,
                 "text": text, "at": int(time.time() * 1000)}
            )

    elif t == "sound":
        sid = str(msg.get("sound", ""))[:64]
        if not sid:
            return
        if sid.startswith("file:"):
            stem = sid[5:]
            if not any(f.stem == stem and f.suffix.lower() in AUDIO_EXTS
                       for f in SOUNDS_DIR.iterdir() if f.is_file()):
                return
        elif sid not in BUILTIN_SOUNDS:
            return

        force = bool(msg.get("force")) and peer.is_admin
        if not force and not sound_allowed(peer):
            await room.send_to(peer.id, {"t": "sound-ratelimit"})
            return
        await room.broadcast(
            {"t": "sound", "sound": sid, "from": peer.id, "name": peer.name,
             "at": int(time.time() * 1000)}
        )

    elif t == "admin-login":
        if str(msg.get("password", "")) == ADMIN_PASSWORD:
            peer.is_admin = True
            await room.send_to(peer.id, {"t": "admin-ok",
                "peers": [p.public() for p in room.peers.values()]})
            await room.broadcast({"t": "peer-state", "id": peer.id,
                                  "muted": peer.muted, "video": peer.video,
                                  "screen": peer.screen, "isAdmin": True},
                                 exclude=peer.id)
            log.info("admin login room=%s peer=%s", room.id, peer.id)
        else:
            await room.send_to(peer.id, {"t": "admin-no"})

    elif t == "admin-mute":
        if not peer.is_admin:
            return
        target = msg.get("target")
        muted = bool(msg.get("muted"))
        tp = room.peers.get(target)
        if tp is None:
            return
        tp.muted_by_admin = muted
        if muted:
            tp.muted = True
        await room.broadcast({
            "t": "peer-state", "id": tp.id,
            "muted": tp.muted, "video": tp.video, "screen": tp.screen,
            "mutedByAdmin": tp.muted_by_admin,
        })
        if muted:
            await room.send_to(tp.id, {"t": "you-muted"})

    elif t == "admin-kick":
        if not peer.is_admin:
            return
        target = msg.get("target")
        tp = room.peers.get(target)
        if tp is None:
            return
        await room.send_to(tp.id, {"t": "you-kicked"})
        try:
            await tp.ws.close(code=1008)
        except Exception:
            pass


@app.websocket("/ws/{room_id}")
async def signaling(ws: WebSocket, room_id: str) -> None:
    if not room_id or len(room_id) > 64:
        await ws.close(code=1008)
        return

    await ws.accept()

    try:
        hello = json.loads(await asyncio.wait_for(ws.receive_text(), HELLO_TIMEOUT))
        if not isinstance(hello, dict):
            raise ValueError
    except Exception:
        await ws.close(code=1008)
        return

    name = str(hello.get("name") or "Guest").strip()[:32] or "Guest"
    peer_id = secrets.token_urlsafe(9)

    async with ROOMS_LOCK:
        room = ROOMS.get(room_id)
        if room is None:
            room = Room(room_id)
            ROOMS[room_id] = room

    async with room.lock:
        if len(room.peers) >= MAX_PEERS:
            await ws.close(code=1013)
            return
        peer = Peer(peer_id, name, ws)
        roster = [p.public() for p in room.peers.values()]
        room.peers[peer_id] = peer

    await ws.send_text(json.dumps(
        {"t": "welcome", "id": peer_id, "peers": roster}, separators=SEP
    ))
    await room.broadcast({"t": "peer-joined", "peer": peer.public()}, exclude=peer_id)
    log.info("join room=%s peer=%s name=%s size=%d",
             room_id, peer_id, name, len(room.peers))

    try:
        while True:
            raw = await ws.receive_text()
            if len(raw) > MAX_MSG_BYTES:
                continue
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            if isinstance(msg, dict):
                await handle_signal(room, peer, msg)
    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception("ws error room=%s peer=%s", room_id, peer_id)
    finally:
        async with room.lock:
            room.peers.pop(peer_id, None)
            empty = not room.peers
        await room.broadcast({"t": "peer-left", "id": peer_id})
        if empty:
            async with ROOMS_LOCK:
                if ROOMS.get(room_id) is room and not room.peers:
                    ROOMS.pop(room_id, None)
        log.info("leave room=%s peer=%s", room_id, peer_id)


# ---------------------------------------------------------------------------
def main() -> None:
    import uvicorn

    ap = argparse.ArgumentParser(description="VoiceChat server")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--reload", action="store_true")
    ap.add_argument("--ssl-keyfile", default=None)
    ap.add_argument("--ssl-certfile", default=None)
    args = ap.parse_args()

    scheme = "https" if args.ssl_certfile else "http"
    custom = scan_custom_sounds()

    print()
    print("=" * 60)
    print("  VoiceChat server starting")
    print("=" * 60)
    print(f"  URL            : {scheme}://{args.host}:{args.port}")
    print(f"  Uploads folder : {FILES_DIR}")
    print(f"  Sounds folder  : {SOUNDS_DIR}")
    if custom:
        print(f"  Custom sounds  : {len(custom)} found")
    print()
    print(f"  *** ADMIN PASSWORD: {ADMIN_PASSWORD} ***")
    print()
    print("  Share this with whoever should be able to mute/kick.")
    print("  It is different every time the server restarts.")
    print("=" * 60)
    print()

    uvicorn.run(
        app, host=args.host, port=args.port, reload=args.reload,
        log_level="info", access_log=False,
        ws_ping_interval=20, ws_ping_timeout=20,
        ssl_keyfile=args.ssl_keyfile, ssl_certfile=args.ssl_certfile,
    )


if __name__ == "__main__":
    main()