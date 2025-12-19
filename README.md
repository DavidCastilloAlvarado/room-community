# 📹🔊 WebRTC Audio & Video Broadcast

Browser-to-browser audio and video broadcasting using WebRTC. One broadcaster, multiple viewers with real-time chat.

## Features

- 🎥 **Live Video & Audio Broadcasting**: WebRTC-based peer-to-peer streaming
- 💬 **Real-time Chat**: Viewers can send messages to broadcaster and other viewers
- 👥 **Multiple Viewers**: Support for simultaneous viewers with automatic connection management
- ⏱️ **TTL Cache**: Automatic channel cleanup after 1 hour of inactivity
- 🔒 **SSL Support**: Optional HTTPS for network camera/microphone access
- 📱 **Responsive Design**: Works on desktop and mobile devices

## How It Works

1. **Server (Python)**: Flask-SocketIO handles WebRTC signaling - connects broadcaster to viewers
2. **Browser**: Captures camera/mic and streams directly peer-to-peer (no video processing on server!)
3. **Direct Connection**: After setup, video/audio flows directly between browsers
4. **Chat System**: Messages routed through server to all participants

## Project Structure

```
stream/
├── broadcast/              # Main application package
│   ├── __init__.py        # Package initialization
│   ├── app.py             # Flask app factory and SocketIO setup
│   ├── routes.py          # HTTP routes (index page)
│   ├── events.py          # Socket.IO event handlers
│   └── schemas.py         # Marshmallow validation schemas
├── templates/             # HTML templates
│   └── broadcast.html     # Main broadcast interface
├── run.py                 # Application entry point
├── pyproject.toml         # Poetry dependencies and configuration
└── README.md              # This file
```

## Installation

Install dependencies using Poetry:

```bash
poetry install
```

## Running the Server

### Basic (HTTP - localhost only)

```bash
poetry run python run.py
```

Server runs on `http://0.0.0.0:3000`

### With SSL (HTTPS - for network access)

Generate self-signed certificate:

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj '/CN=localhost'
```

Run server (will auto-detect SSL certificates):

```bash
poetry run python run.py
```

Server runs on `https://0.0.0.0:3000`

## Usage

### Broadcaster Mode

1. Open: `http://localhost:3000?broadcaster=true`
2. Click **"Start Broadcasting"** in the header
3. Allow camera/mic access when prompted
4. Share your channel ID with viewers
5. View incoming chat messages from viewers

### Viewer Mode

1. Open: `http://localhost:3000?viewer=true`
2. Enter the channel ID or select from available broadcasts
3. Automatically connect and view the stream
4. Set your display name for chat
5. Send messages to broadcaster and other viewers

### Mode Switching

Use the header buttons to switch between modes:
- **Broadcaster Mode**: Start your own broadcast
- **Viewer Mode**: Watch someone else's broadcast

## Development

### Code Formatting & Linting

The project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Run linter and formatter
poetry run poe ruff

# Or run individually
poetry run ruff check . --fix
poetry run ruff format .
```

### Configuration

Ruff is configured in `pyproject.toml` with:
- Line length: 100 characters
- Python 3.12 target
- Auto-fixing enabled
- Standard Python best practices

## Technical Details

### Dependencies

- **Flask**: Web framework
- **Flask-SocketIO**: WebSocket support for real-time communication
- **python-socketio**: Socket.IO Python client/server
- **Marshmallow**: Data validation and serialization
- **cachetools**: TTL-based cache for channel management
- **Ruff**: Fast Python linter and formatter

### Channel Management

- Channels are stored in-memory using `TTLCache`
- Maximum 100 channels
- Automatic expiration after 1 hour of inactivity
- Last activity timestamp updates on viewer joins and WebRTC signaling

### WebRTC Signaling Flow

1. Broadcaster creates channel and gets channel ID
2. Viewer joins channel with channel ID
3. Server facilitates SDP offer/answer exchange
4. ICE candidates exchanged through server
5. Peer-to-peer connection established
6. Server continues routing chat messages

## Important Notes

- ⚠️ **Server required**: Server MUST be running for new connections and chat
- 🔗 **P2P streaming**: Once connected, video/audio streams are peer-to-peer (direct browser-to-browser)
- 💾 **No persistence**: Channels and messages are ephemeral (not saved to database)
- 🌐 **HTTPS for network**: Camera/mic access requires HTTPS when accessing from network devices
- 📱 **Browser compatibility**: Requires modern browser with WebRTC support (Chrome, Firefox, Safari, Edge)

## Troubleshooting

### Camera/Mic not accessible on mobile
- Ensure you're using HTTPS (generate SSL certificate)
- Check browser permissions for camera/microphone

### Viewer can't connect
- Verify server is running
- Check channel ID is correct
- Ensure firewall allows port 3000

### Chat messages not appearing
- Viewers must set an alias before sending messages
- Check browser console for JavaScript errors
