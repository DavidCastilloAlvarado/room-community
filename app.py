import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import cv2

# This configuration is necessary for some browsers to handle the connection
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

st.set_page_config(page_title="Camera Stream", layout="wide")

st.title("📹 Live Camera Stream")
st.write("Stream your PC camera to the web. Anyone accessing this page can see the camera feed.")

# Simple camera streamer
webrtc_ctx = webrtc_streamer(
    key="camera-stream",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTC_CONFIGURATION,
    media_stream_constraints={
        "video": {"width": {"ideal": 1280}, "height": {"ideal": 720}},
        "audio": True
    },
    async_processing=True,
)

if webrtc_ctx.state.playing:
    st.success("🔴 LIVE - Camera is streaming!")
    st.info("Share this URL with others to let them see your camera: http://192.168.18.140:3000")
else:
    st.warning("⚪ Camera not active. Click START above to begin streaming.")

st.sidebar.header("Instructions")
st.sidebar.markdown("""
**Broadcasting (Your PC):**
1. Click **START** button above
2. Allow camera & microphone access
3. You should see your camera feed

**Viewing (Other devices):**
1. Open: `http://192.168.18.140:3000`
2. Click **START** 
3. Allow camera access when prompted
4. You'll see the camera feed

**Note:** Due to WebRTC peer-to-peer nature, each viewer needs to click START. For true one-to-many broadcasting, you'd need a media server.
""")
