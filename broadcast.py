#!/usr/bin/env python3
"""
WebRTC Broadcast Server - Audio & Video
Broadcasts your PC camera and microphone to multiple viewers using WebRTC
"""
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from cachetools import TTLCache
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Track channels/rooms with 1-hour TTL (auto-cleanup)
# TTLCache(maxsize=100, ttl=3600) - stores max 100 channels, each expires after 1 hour
channels = TTLCache(maxsize=100, ttl=3600)

@app.route('/')
def index():
    """Main page - detects if user should be broadcaster or viewer."""
    return render_template('broadcast.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")
    emit('client_id', {'id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")
    
    # Find and clean up from any channel
    for channel_id, channel_data in list(channels.items()):
        if channel_data['broadcaster'] == request.sid:
            print(f"Broadcaster disconnected from channel: {channel_id}")
            # Notify viewers in this channel
            for viewer in channel_data['viewers']:
                emit('broadcaster_disconnected', room=viewer)
            # Remove channel
            del channels[channel_id]
        elif request.sid in channel_data['viewers']:
            channel_data['viewers'].remove(request.sid)

@socketio.on('join_as_broadcaster')
def handle_join_broadcaster(data=None):
    """Handle broadcaster joining - creates a new channel."""
    import uuid
    channel_id = data.get('channel_id') if data else None
    
    if not channel_id:
        # Generate unique channel ID
        channel_id = str(uuid.uuid4())[:8]
    
    # Check if channel already exists
    if channel_id in channels:
        emit('error', {'message': f'Channel {channel_id} already has a broadcaster'})
        return
    
    # Create new channel (TTL automatically starts from insertion)
    channels[channel_id] = {
        'broadcaster': request.sid,
        'viewers': set(),
        'created_at': time.time(),
        'last_activity': time.time()
    }
    
    print(f"Broadcaster joined channel: {channel_id} (sid: {request.sid}) [TTL: 1h]")
    emit('broadcaster_ready', {'id': request.sid, 'channel_id': channel_id})

@socketio.on('join_as_viewer')
def handle_join_viewer(data=None):
    """Handle viewer joining a specific channel."""
    channel_id = data.get('channel_id') if data else None
    
    if not channel_id:
        # Return list of active channels from TTL cache
        active_channels = [
            {
                'id': cid,
                'broadcaster_sid': cdata['broadcaster'],
                'created_at': cdata['created_at'],
                'age_seconds': int(time.time() - cdata['created_at']),
                'last_activity': cdata.get('last_activity', cdata['created_at'])
            }
            for cid, cdata in list(channels.items())  # list() to avoid dict size change during iteration
        ]
        emit('channel_list', {'channels': active_channels})
        return
    
    # Join specific channel
    if channel_id not in channels:
        emit('error', {'message': f'Channel {channel_id} not found or expired'})
        return
    
    # Update last activity to refresh TTL
    channel_data = channels[channel_id]
    channel_data['viewers'].add(request.sid)
    channel_data['last_activity'] = time.time()
    channels[channel_id] = channel_data  # Re-insert to refresh TTL
    
    broadcaster_id = channel_data['broadcaster']
    
    print(f"Viewer joined channel {channel_id}: {request.sid} (Total: {len(channel_data['viewers'])})")
    emit('broadcaster_available', {
        'broadcaster_id': broadcaster_id,
        'channel_id': channel_id
    })

@socketio.on('offer')
def handle_offer(data):
    """Forward WebRTC offer from viewer to broadcaster."""
    target = data.get('target')
    print(f"Forwarding offer from {request.sid} to {target}")
    
    # Refresh TTL on channel activity
    for cid, cdata in list(channels.items()):
        if cdata['broadcaster'] == target or request.sid in cdata['viewers']:
            cdata['last_activity'] = time.time()
            channels[cid] = cdata
            break
    
    emit('offer', {
        'sdp': data['sdp'],
        'sender': request.sid
    }, room=target)

@socketio.on('answer')
def handle_answer(data):
    """Forward WebRTC answer from broadcaster to viewer."""
    target = data.get('target')
    print(f"Forwarding answer from {request.sid} to {target}")
    
    # Refresh TTL on channel activity
    for cid, cdata in list(channels.items()):
        if cdata['broadcaster'] == request.sid or target in cdata['viewers']:
            cdata['last_activity'] = time.time()
            channels[cid] = cdata
            break
    
    emit('answer', {
        'sdp': data['sdp'],
        'sender': request.sid
    }, room=target)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    """Forward ICE candidate between peers."""
    target = data.get('target')
    if target:
        emit('ice_candidate', {
            'candidate': data['candidate'],
            'sender': request.sid
        }, room=target)

@socketio.on('stop_broadcast')
def handle_stop_broadcast(data):
    """Handle broadcaster stopping their broadcast."""
    channel_id = data.get('channel_id')
    
    if channel_id and channel_id in channels:
        if channels[channel_id]['broadcaster'] == request.sid:
            print(f"Broadcaster stopped broadcast on channel: {channel_id}")
            # Notify all viewers
            for viewer in channels[channel_id]['viewers']:
                emit('broadcaster_stopped', {'channel_id': channel_id}, room=viewer)

if __name__ == '__main__':
    import os
    import ssl
    
    # Check for SSL certificates
    cert_file = 'cert.pem'
    key_file = 'key.pem'
    
    use_ssl = os.path.exists(cert_file) and os.path.exists(key_file)
    protocol = 'https' if use_ssl else 'http'
    
    print("=" * 70)
    print("📹🔊 AUDIO & VIDEO BROADCAST SERVER")
    print("=" * 70)
    
    if use_ssl:
        print(f"🔒 Running with HTTPS (SSL enabled)")
        print(f"🔴 Server: {protocol}://0.0.0.0:3000")
        print(f"📱 PC: {protocol}://localhost:3000")
        print(f"📱 Network: {protocol}://192.168.18.140:3000")
        print("\n⚠️  Accept the security warning in your browser (self-signed cert)")
    else:
        print(f"⚠️  Running without HTTPS - camera/mic may not work on network!")
        print(f"🔴 Server: {protocol}://0.0.0.0:3000")
        print(f"📱 PC only: {protocol}://localhost:3000")
        print("\n💡 To enable HTTPS (required for camera access via network):")
        print("   Run: openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj '/CN=localhost'")
    
    print("\n📌 Instructions:")
    print("   1. Open on your PC first - you'll be the BROADCASTER")
    print("   2. Click START and allow camera/mic access")
    print("   3. Open on other devices - they'll be VIEWERS")
    print("   4. Viewers will see and hear your broadcast!")
    print("\n💾 Cache: TTL-based LRU (max 100 channels, 1-hour auto-expiration)")
    print("=" * 70)
    
    if use_ssl:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        socketio.run(app, host='0.0.0.0', port=3000, debug=False, ssl_context=context, allow_unsafe_werkzeug=True)
    else:
        socketio.run(app, host='0.0.0.0', port=3000, debug=False, allow_unsafe_werkzeug=True)
