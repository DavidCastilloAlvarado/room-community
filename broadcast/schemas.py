"""Validation schemas for broadcast server."""
from marshmallow import Schema, fields, validates, ValidationError, validate
import re


class ChannelIdField(fields.String):
    """Custom field for alphanumeric channel IDs."""
    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        if value and not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValidationError('Channel ID must be alphanumeric (letters, numbers, _, -)')
        return value


class BroadcasterJoinSchema(Schema):
    """Schema for broadcaster join requests."""
    channel_id = ChannelIdField(allow_none=True, validate=validate.Length(max=20))
    force = fields.Boolean(load_default=False)


class ViewerJoinSchema(Schema):
    """Schema for viewer join requests."""
    channel_id = ChannelIdField(allow_none=True, validate=validate.Length(max=20))


class MessageSchema(Schema):
    """Schema for viewer messages."""
    channel_id = ChannelIdField(required=True, validate=validate.Length(min=1, max=20))
    message = fields.String(required=True, validate=validate.Length(min=1, max=200))
    
    @validates('message')
    def validate_message(self, value, **kwargs):
        # Block only dangerous control characters, allow Unicode (including emojis)
        # Block: NULL, control chars (0x00-0x1F), DEL (0x7F), but allow newlines/tabs
        if re.search(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', value):
            raise ValidationError('Message contains invalid control characters')
        
        # Prevent potential XSS by blocking script-like patterns
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onload\s*='
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError('Message contains potentially dangerous content')


class StopBroadcastSchema(Schema):
    """Schema for stop broadcast requests."""
    channel_id = ChannelIdField(required=True, validate=validate.Length(min=1, max=20))


class SetAliasSchema(Schema):
    """Schema for setting viewer alias."""
    channel_id = ChannelIdField(required=True, validate=validate.Length(min=1, max=20))
    alias = fields.String(
        required=True,
        validate=validate.Length(min=5, max=20)
    )
    
    @validates('alias')
    def validate_alias(self, value, **kwargs):
        # Allow letters, numbers, spaces, underscores, hyphens
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', value.strip()):
            raise ValidationError('Alias must contain only letters, numbers, spaces, _ or -')


# Schema instances
broadcaster_join_schema = BroadcasterJoinSchema()
viewer_join_schema = ViewerJoinSchema()
message_schema = MessageSchema()
stop_broadcast_schema = StopBroadcastSchema()
set_alias_schema = SetAliasSchema()
