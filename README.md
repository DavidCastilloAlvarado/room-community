# 📹🔊 WebRTC Audio & Video Broadcast

Browser-to-browser audio and video broadcasting using WebRTC. One broadcaster, multiple viewers.

## How It Works

1. **Server (Python)**: Handles WebRTC signaling via Socket.IO - connects broadcaster to viewers
2. **Browser**: Captures camera/mic and streams directly peer-to-peer (no video processing on server!)
3. **Direct Connection**: After setup, video/audio flows directly between browsers

## Installation

```bash
poetry install
```

## Running

```bash
poetry run python broadcast.py
```

Server runs on port 3000

## Usage

**Broadcaster (Your PC):**
1. Open: http://localhost:3000
2. Click "START BROADCASTING"
3. Allow camera/mic access
4. You're now live!

**Viewers (Any Device):**
1. Open: http://192.168.18.140:3000?viewer=true
2. Click "WATCH STREAM"
3. See and hear the broadcast!

## Important Notes

- Server MUST be running for new connections
- Once connected, streams are peer-to-peer (direct browser-to-browser)
- If server crashes after connection, existing viewers stay connected
- No server-side video processing - all happens in browsers
- Multiple viewers supported simultaneously
