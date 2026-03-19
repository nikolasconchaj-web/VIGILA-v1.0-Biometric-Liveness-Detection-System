import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import numpy as np

# Configuración de la página épica
st.set_page_config(page_title="VIGILA v1.0 - NC Space", page_icon="👁️")
st.title("👁️ VIGILA: Sistema de Verificación Biométrica")
st.subheader("Prueba de Vida: Parpadea para validar")

# Cargamos los detectores (Haar Cascades)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.blink_count = 0
        self.is_eye_closed = False

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            roi_gray = gray[y:y + h, x:x + w]
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10)

            # Lógica de parpadeo
            if len(eyes) == 0:
                self.is_eye_closed = True
            else:
                if self.is_eye_closed:
                    self.blink_count += 1
                    self.is_eye_closed = False

            # Texto de estado en el video
            status = "VERIFICADO" if self.blink_count >= 3 else f"Parpadeos: {self.blink_count}/3"
            color = (0, 255, 0) if self.blink_count >= 3 else (0, 255, 255)
            
            cv2.putText(img, status, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        return img

# El "Mágico" Streamer de Cámara para Web
ctx = webrtc_streamer(key="vigila-captcha", video_transformer_factory=VideoProcessor)

if ctx.video_transformer:
    st.write(f"### Estado del CAPTCHA: {ctx.video_transformer.blink_count} parpadeos detectados.")
    if ctx.video_transformer.blink_count >= 3:
        st.success("✅ ¡HUMANO VALIDADO! Acceso concedido.")
        st.balloons() # ¡Festejo con globos!
