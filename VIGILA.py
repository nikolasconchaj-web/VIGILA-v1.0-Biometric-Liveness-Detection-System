import streamlit as st
from streamlit_webrtc import webrtc_streamer
import cv2
import av 
import time


st.set_page_config(page_title="VIGILA v2.4 - Friendly Edition", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #f0f0f0; }
    .stTitle { color: #00ffcc; font-family: 'Courier New', Courier, monospace; text-shadow: 2px 2px 4px #000000; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ VIGILA v2.4: Escudo Biométrico")


face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')


if "blink_count" not in st.session_state:
    st.session_state.blink_count = 0
    st.session_state.smile_duration = 0
    st.session_state.last_eye_time = time.time()
    st.session_state.is_eye_closed = False
    st.session_state.verified = False

def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    status = "BUSCANDO ROSTRO..."

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10)
        
       
        if len(eyes) == 0:
            st.session_state.is_eye_closed = True
        else:
            if st.session_state.is_eye_closed:
                st.session_state.blink_count += 1
                st.session_state.is_eye_closed = False
            st.session_state.last_eye_time = time.time()

        
        if st.session_state.blink_count >= 2:
            smiles = smile_cascade.detectMultiScale(roi_gray, 1.2, 12, minSize=(30, 30))
            if len(smiles) > 0:
                st.session_state.smile_duration += 0.1 
            else:
                st.session_state.smile_duration = 0
            status = "FASE 2: SONRÍE"
        else:
            status = f"FASE 1: PARPADEA ({st.session_state.blink_count}/2)"

        if st.session_state.blink_count >= 2 and st.session_state.smile_duration >= 5:
            st.session_state.verified = True
            status = "VERIFICADO"

        
        color = (0, 255, 0) if st.session_state.verified else (0, 255, 255)
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        cv2.putText(img, status, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    return av.VideoFrame.from_ndarray(img, format="bgr24")


webrtc_streamer(
    key="vigila-v24",
    video_frame_callback=video_frame_callback,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}, 
    media_stream_constraints={"video": True, "audio": False},
)

if st.session_state.verified:
    st.success("✅ ¡HUMANO VALIDADO!")
    st.balloons()
