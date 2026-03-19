import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import numpy as np
import time

st.set_page_config(page_title="VIGILA v2.1 - Seguridad Biométrica", page_icon="🛡️")
st.title("🛡️ VIGILA: Sistema de Seguridad de Élite")
st.markdown("---")

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
        self.status_msg = "BUSCANDO SUJETO..."
        self.fully_verified = False

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            self.status_msg = "CÁMARA VACÍA"
        
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10)
            
            if len(eyes) == 0 and not self.is_eye_closed:
                color = (0, 0, 255) 
                self.status_msg = "ALERTA: POSIBLE FRAUDE / FOTO DETECTADA"
            else:
                color = (0, 255, 0) if self.fully_verified else (0, 255, 255) 
                
             
                if len(eyes) == 0:
                    self.is_eye_closed = True
                else:
                    if self.is_eye_closed:
                        self.blink_count += 1
                        self.is_eye_closed = False
                
              
                if self.blink_count >= 2:
                    self.status_msg = "FASE 2: MANTÉN LA SONRISA"
                    smiles = smile_cascade.detectMultiScale(roi_gray, 1.8, 20)
                    if len(smiles) > 0:
                        if not self.is_smiling:
                            self.is_smiling = True
                            self.smile_start_time = time.time()
                        self.smile_duration = time.time() - self.smile_start_time
                    else:
                        self.is_smiling = False
                        self.smile_duration = 0
                else:
                    self.status_msg = f"FASE 1: PARPADEA ({self.blink_count}/2)"

       
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            cv2.putText(img, self.status_msg, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

          
            if self.blink_count >= 2 and self.smile_duration >= 2.0:
                self.fully_verified = True
                self.status_msg = "ACCESO CONCEDIDO - HUMANO VERIFICADO"

        return img

col1, col2 = st.columns([2, 1])

with col1:
    ctx = webrtc_streamer(key="vigila-v2-1", video_transformer_factory=VideoProcessor)

with col2:
    st.write("### Panel de Control")
    if ctx.video_transformer:
        st.info(f"Estado: {ctx.video_transformer.status_msg}")
        if ctx.video_transformer.fully_verified:
            st.success("✅ Verificación Exitosa")
            st.balloons()
        elif "ALERTA" in ctx.video_transformer.status_msg:
            st.error("⚠️ Actividad Sospechosa")
