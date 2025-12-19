"""Socket.IO event handlers for broadcast server."""
from flask import request
from flask_socketio import emit
from marshmallow import ValidationError
import time
import uuid

from .app import socketio, channels
from .schemas import (
    broadcaster_join_schema,
    viewer_join_schema,
    message_schema,
    stop_broadcast_schema,
    set_alias_schema
)


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
    # Validate input
    try:
        data = data or {}
        validated_data = broadcaster_join_schema.load(data)
    except ValidationError as err:
        emit('error', {'message': f'Invalid data: {err.messages}'})
        return
    
    channel_id = validated_data.get('channel_id')
    
    if not channel_id:
        # Generate unique channel ID (alphanumeric, 8 chars)
        channel_id = str(uuid.uuid4()).replace('-', '')[:8]
    
    # Check if channel already exists
    if channel_id in channels:
        emit('error', {'message': f'Channel {channel_id} already has a broadcaster'})
        return
    
    # Create new channel (TTL automatically starts from insertion)
    channels[channel_id] = {
        'broadcaster': request.sid,
        'viewers': set(),
        'viewer_aliases': {},  # {viewer_sid: alias}
        'created_at': time.time(),
        'last_activity': time.time()
    }
    
    print(f"Broadcaster joined channel: {channel_id} (sid: {request.sid}) [TTL: 1h]")
    emit('broadcaster_ready', {'id': request.sid, 'channel_id': channel_id})


@socketio.on('join_as_viewer')
def handle_join_viewer(data=None):
    """Handle viewer joining a specific channel."""
    # Validate input
    try:
        data = data or {}
        validated_data = viewer_join_schema.load(data)
    except ValidationError as err:
        emit('error', {'message': f'Invalid data: {err.messages}'})
        return
    
    channel_id = validated_data.get('channel_id')
    
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
    # Validate input
    try:
        validated_data = stop_broadcast_schema.load(data)
    except ValidationError as err:
        emit('error', {'message': f'Invalid data: {err.messages}'})
        return
    
    channel_id = validated_data['channel_id']
    
    if channel_id not in channels:
        emit('error', {'message': 'Channel not found or expired'})
        return
    
    if channels[channel_id]['broadcaster'] != request.sid:
        emit('error', {'message': 'You are not the broadcaster of this channel'})
        return
    
    print(f"Broadcaster stopped broadcast on channel: {channel_id}")
    # Notify all viewers
    for viewer in channels[channel_id]['viewers']:
        emit('broadcaster_stopped', {'channel_id': channel_id}, room=viewer)


@socketio.on('set_alias')
def handle_set_alias(data):
    """Set viewer alias for chat messages."""
    # Validate input
    try:
        validated_data = set_alias_schema.load(data)
    except ValidationError as err:
        emit('error', {'message': f'Invalid alias: {err.messages}'})
        return
    
    channel_id = validated_data['channel_id']
    alias = validated_data['alias'].strip()
    
    if channel_id not in channels:
        emit('error', {'message': 'Channel not found or expired'})
        return
    
    # Only allow viewers to set aliases
    if request.sid not in channels[channel_id]['viewers']:
        emit('error', {'message': 'You must be a viewer in this channel'})
        return
    
    # Store alias
    channels[channel_id]['viewer_aliases'][request.sid] = alias
    print(f"Viewer {request.sid[:8]} set alias: {alias} in channel {channel_id}")
    
    emit('alias_set', {'alias': alias, 'success': True})


@socketio.on('send_message')
def handle_send_message(data):
    """Forward viewer message to broadcaster (ephemeral - no persistence)."""
    # Validate input
    try:
        validated_data = message_schema.load(data)
    except ValidationError as err:
        emit('error', {'message': f'Invalid message: {err.messages}'})
        return
    
    channel_id = validated_data['channel_id']
    message = validated_data['message'].strip()
    
    if channel_id not in channels:
        emit('error', {'message': 'Channel not found or expired'})
        return
    
    # Only allow viewers to send messages
    if request.sid not in channels[channel_id]['viewers']:
        emit('error', {'message': 'You must be a viewer in this channel to send messages'})
        return
    
    # Get viewer alias or use short ID
    viewer_name = channels[channel_id]['viewer_aliases'].get(request.sid, f'Viewer-{request.sid[:8]}')
    broadcaster_sid = channels[channel_id]['broadcaster']
    print(f"Message from {viewer_name} to channel {channel_id}: {message[:50]}...")
    
    # Forward to broadcaster
    emit('new_message', {
        'sender_id': viewer_name,
        'message': message,
        'timestamp': time.time()
    }, room=broadcaster_sid)
