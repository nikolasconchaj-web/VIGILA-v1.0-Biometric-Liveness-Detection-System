import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import cv2
import av
import threading

st.set_page_config(page_title="VIGILA v2.5 - Professional Biometrics", page_icon="🛡️")
st.title("🛡️ VIGILA v2.5")

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

class FaceProcessor(VideoProcessorBase):
    def __init__(self):
        self.blink_count = 0
        self.is_eye_closed = False
        self.smile_frames = 0
        self.verified = False
        self.lock = threading.Lock() 
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        with self.lock:
            status = "BUSCANDO HUMANO..."
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y + h, x:x + w]
                eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10)
           
                if len(eyes) == 0:
                    self.is_eye_closed = True
                else:
                    if self.is_eye_closed:
                        self.blink_count += 1
                        self.is_eye_closed = False

                if self.blink_count >= 2:
                    smiles = smile_cascade.detectMultiScale(roi_gray, 1.3, 25)
                    if len(smiles) > 0:
                        self.smile_frames += 1
                    status = f"FASE 2: SONRÍE ({min(100, self.smile_frames*5)}%)"
                else:
                    status = f"FASE 1: PARPADEA ({self.blink_count}/2)"

                if self.blink_count >= 2 and self.smile_frames >= 15:
                    self.verified = True
                    status = "✅ VERIFICADO"

         
                color = (0, 255, 0) if self.verified else (0, 255, 255)
                cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(img, status, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

ctx = webrtc_streamer(
    key="vigila-pro-v25",
    video_processor_factory=FaceProcessor,
    rtc_configuration=RTC_CONFIGURATION,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True, 
)

if ctx.video_processor:
    with st.expander("Ver estadísticas en tiempo real"):
        st.write(f"Parpadeos detectados: {ctx.video_processor.blink_count}")
        if ctx.video_processor.verified:
            st.success("Acceso Concedido")
            st.balloons()
