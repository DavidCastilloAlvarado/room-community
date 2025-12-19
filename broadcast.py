#!/usr/bin/env python3
"""
WebRTC Broadcast Server - Audio & Video
Broadcasts your PC camera and microphone to multiple viewers using WebRTC
"""
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Track connected clients
broadcaster_id = None
viewers = set()

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
    global broadcaster_id
    print(f"Client disconnected: {request.sid}")
    
    if request.sid == broadcaster_id:
        print("Broadcaster disconnected!")
        broadcaster_id = None
        # Notify all viewers
        emit('broadcaster_disconnected', broadcast=True)
    elif request.sid in viewers:
        viewers.remove(request.sid)

@socketio.on('join_as_broadcaster')
def handle_join_broadcaster():
    """Handle broadcaster joining."""
    global broadcaster_id
    
    if broadcaster_id is not None:
        emit('error', {'message': 'A broadcaster is already active'})
        return
    
    broadcaster_id = request.sid
    print(f"Broadcaster joined: {broadcaster_id}")
    emit('broadcaster_ready', {'id': broadcaster_id})
    # Notify all viewers that broadcaster is ready
    emit('broadcaster_joined', {'id': broadcaster_id}, broadcast=True, include_self=False)

@socketio.on('join_as_viewer')
def handle_join_viewer():
    """Handle viewer joining."""
    viewers.add(request.sid)
    print(f"Viewer joined: {request.sid} (Total viewers: {len(viewers)})")
    
    # Tell viewer about broadcaster
    if broadcaster_id:
        emit('broadcaster_available', {'broadcaster_id': broadcaster_id})
    else:
        emit('waiting_for_broadcaster')

@socketio.on('offer')
def handle_offer(data):
    """Forward WebRTC offer from viewer to broadcaster."""
    target = data.get('target')
    print(f"Forwarding offer from {request.sid} to {target}")
    emit('offer', {
        'sdp': data['sdp'],
        'sender': request.sid
    }, room=target)

@socketio.on('answer')
def handle_answer(data):
    """Forward WebRTC answer from broadcaster to viewer."""
    target = data.get('target')
    print(f"Forwarding answer from {request.sid} to {target}")
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

if __name__ == '__main__':
    print("=" * 70)
    print("📹🔊 AUDIO & VIDEO BROADCAST SERVER")
    print("=" * 70)
    print(f"🔴 Server running on: http://0.0.0.0:3000")
    print(f"📱 Access from PC: http://localhost:3000")
    print(f"📱 Access from network: http://192.168.18.140:3000")
    print("\n📌 Instructions:")
    print("   1. Open on your PC first - you'll be the BROADCASTER")
    print("   2. Click START and allow camera/mic access")
    print("   3. Open on other devices - they'll be VIEWERS")
    print("   4. Viewers will see and hear your broadcast!")
    print("=" * 70)
    socketio.run(app, host='0.0.0.0', port=3000, debug=False, allow_unsafe_werkzeug=True)
