import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import numpy as np
import time


st.set_page_config(page_title="VIGILA v2.2 - Biometric Security", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTitle { color: #00ffcc; font-family: 'Courier New', Courier, monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ VIGILA v2.2: Escudo Biométrico NC-Space")
st.write("---")

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.blink_count = 0
        self.is_eye_closed = False
        self.smile_duration = 0
        self.smile_start_time = None
        self.is_smiling = False
        self.fully_verified = False
        self.status_text = "ESPERANDO SUJETO..."
        self.last_eye_time = time.time()

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10)
            
       
            if len(eyes) == 0:
              
                self.is_eye_closed = True
               
                if time.time() - self.last_eye_time > 2.0:
                    self.status_text = "ALERTA: PRUEBA DE VIDA REQUERIDA"
            else:
                self.last_eye_time = time.time()
                if self.is_eye_closed:
                    self.blink_count += 1
                    self.is_eye_closed = False
                
                if self.blink_count < 2:
                    self.status_text = f"FASE 1: PARPADEA ({self.blink_count}/2)"

            if self.blink_count >= 2:
                self.status_text = "FASE 2: MANTÉN LA SONRISA (2s)"
                smiles = smile_cascade.detectMultiScale(roi_gray, 1.7, 22)
                
                if len(smiles) > 0:
                    if not self.is_smiling:
                        self.is_smiling = True
                        self.smile_start_time = time.time()
                    self.smile_duration = time.time() - self.smile_start_time
                else:
                    self.is_smiling = False
                    self.smile_duration = 0

            if self.blink_count >= 2 and self.smile_duration >= 2.0:
                self.fully_verified = True
                self.status_text = "VERIFICADO: ACCESO CONCEDIDO"

         
            color = (0, 255, 0) if self.fully_verified else (0, 255, 255)
            if "ALERTA" in self.status_text: color = (0, 0, 255)
            
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            cv2.putText(img, self.status_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return img

col1, col2 = st.columns([2, 1])

with col1:
    st.info("💡 Asegúrate de tener buena iluminación para que los sensores funcionen correctamente.")
    ctx = webrtc_streamer(key="vigila-v22", video_transformer_factory=VideoProcessor)

with col2:
    st.subheader("Panel de Control")
    if ctx.video_transformer:
       
        prog = min(100, int((ctx.video_transformer.smile_duration / 2.0) * 100))
        st.write(f"**Estado:** {ctx.video_transformer.status_text}")
        st.progress(prog, text="Validación de Sonrisa")
        
        if ctx.video_transformer.fully_verified:
            st.success("🔓 Identidad Confirmada")
            st.balloons()
        elif ctx.video_transformer.blink_count >= 2:
            st.warning("Paso 1 completado. ¡Sonríe!")
    else:
        st.write("Esperando a que inicies la cámara...")

st.markdown("---")
st.caption("VIGILA v2.2 por NCubing - Calama, Chile 2026")
