#!/usr/bin/env python3
"""Run the broadcast server."""

import os
import ssl

from broadcast.app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    # Check for SSL certificates
    cert_file = "cert.pem"
    key_file = "key.pem"

    use_ssl = os.path.exists(cert_file) and os.path.exists(key_file)
    protocol = "https" if use_ssl else "http"

    print("=" * 70)
    print("📹🔊 AUDIO & VIDEO BROADCAST SERVER")
    print("=" * 70)

    if use_ssl:
        print("🔒 Running with HTTPS (SSL enabled)")
        print(f"🔴 Server: {protocol}://0.0.0.0:3000")
        print(f"📱 PC: {protocol}://localhost:3000")
        print(f"📱 Network: {protocol}://192.168.18.140:3000")
        print("\n⚠️  Accept the security warning in your browser (self-signed cert)")
    else:
        print("⚠️  Running without HTTPS - camera/mic may not work on network!")
        print(f"🔴 Server: {protocol}://0.0.0.0:3000")
        print(f"📱 PC only: {protocol}://localhost:3000")
        print("\n💡 To enable HTTPS (required for camera access via network):")
        print(
            "   Run: openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj '/CN=localhost'"
        )

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
        socketio.run(
            app,
            host="0.0.0.0",
            port=3000,
            debug=False,
            ssl_context=context,
            allow_unsafe_werkzeug=True,
        )
    else:
        socketio.run(app, host="0.0.0.0", port=3000, debug=False, allow_unsafe_werkzeug=True)
