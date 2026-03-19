import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import numpy as np
import time


st.set_page_config(page_title="VIGILA v2.0 - Doble Factor Biométrico", page_icon="👁️")
st.title("👁️ VIGILA: Sistema de Verificación Biométrica")
st.subheader("Fase 1: Parpadea | Fase 2: Sonríe para validar")


face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.blink_count = 0
        self.is_eye_closed = False
       
        self.is_smiling = False
        self.smile_start_time = None
        self.smile_duration = 0
        self.fully_verified = False

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
           
            face_color = (0, 255, 0) if self.fully_verified else (0, 255, 255)
            cv2.rectangle(img, (x, y), (x + w, y + h), face_color, 2)
            
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = img[y:y + h, x:x + w]

      
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10)
            if len(eyes) == 0:
                self.is_eye_closed = True
            else:
                if self.is_eye_closed:
                    self.blink_count += 1
                    self.is_eye_closed = False

            if self.blink_count >= 2:
             
                smile = smile_cascade.detectMultiScale(roi_gray, 1.8, 20, minSize=(25, 25))
                
                if len(smile) > 0:
                    if not self.is_smiling:
                        self.is_smiling = True
                        self.smile_start_time = time.time()
                    else:
             
                        self.smile_duration = time.time() - self.smile_start_time
                else:
                    self.is_smiling = False
                    self.smile_start_time = None
                    self.smile_duration = 0

            if self.blink_count >= 2 and self.smile_duration >= 2.0:
                self.fully_verified = True
            else:
                self.fully_verified = False

         
            blink_text = f"Parpadeos: {self.blink_count}/2"
            blink_color = (0, 255, 0) if self.blink_count >= 2 else (0, 255, 255)
            cv2.putText(img, blink_text, (x, y - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, blink_color, 2)

            if self.blink_count >= 2:
                smile_text = f"Sonrisa: {int(self.smile_duration)}/2 seg"
                smile_color = (0, 255, 0) if self.smile_duration >= 2.0 else (0, 255, 255)
                cv2.putText(img, smile_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, smile_color, 2)

        return img


ctx = webrtc_streamer(key="vigila-v2", video_transformer_factory=VideoProcessor)

if ctx.video_transformer:
   
    smile_prog = min(100, int((ctx.video_transformer.smile_duration / 2.0) * 100))
    st.progress(smile_prog, text=f"Progreso de Sonrisa Sostenida: {smile_prog}%")

    if ctx.video_transformer.fully_verified:
        st.success("✅ ¡AUTENTICACIÓN COMPLETA! Humano validado con éxito.")
        st.balloons()
