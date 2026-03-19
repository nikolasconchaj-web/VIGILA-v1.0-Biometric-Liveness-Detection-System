import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import numpy as np
import time

# Configuración de Interfaz Profesional
st.set_page_config(page_title="VIGILA v2.3", page_icon="🛡️", layout="wide")

# Estilo visual de "Hacker" / NC-Space
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #f0f0f0; }
    .stTitle { color: #00ffcc; font-family: 'Courier New', Courier, monospace; text-shadow: 2px 2px 4px #000000; }
    .stSubheader { color: #ffcc00; }
    .stWrite { color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ VIGILA v2.3: Escudo Biométrico")
st.write("---")

# Cargamos los detectores de OpenCV (Asegúrate de que no haya errores de ruta)
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

        if len(faces) == 0:
            self.status_text = "CÁMARA VACÍA"

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = img[y:y + h, x:x + w]
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10)
            
            # --- LÓGICA DE PARPADEO (FASE 1) ---
            if len(eyes) == 0:
                self.is_eye_closed = True
                # Tolerancia de 3 segundos para evitar falsos positivos de "BOT"
                if time.time() - self.last_eye_time > 3.0:
                    self.status_text = "ALERTA: PRUEBA DE VIDA REQUERIDA (PARPADEA)"
            else:
                self.last_eye_time = time.time() 
                if self.is_eye_closed:
                    self.blink_count += 1
                    self.is_eye_closed = False
                
                if self.blink_count < 2:
                    self.status_text = f"FASE 1: PARPADEA ({self.blink_count}/2)"

            # --- NUEVA LÓGICA DE SONRISA (FASE 2) - MÁS TOLERANTE ---
            if self.blink_count >= 2:
                self.status_text = "FASE 2: MANTÉN LA SONRISA (2s)"
                
                # ¡AJUSTE CLAVE! Bajamos scaleFactor a 1.2 y minNeighbors a 8.
                # Esto hace que detecte sonrisas más sutiles y no se pierda tan fácil.
                smiles = smile_cascade.detectMultiScale(roi_gray, scaleFactor=1.2, minNeighbors=8, minSize=(30, 30))
                
                # Dibujamos un cuadro amarillo alrededor de la boca si la detecta
                if len(smiles) > 0:
                    if not self.is_smiling:
                        self.is_smiling = True
                        self.smile_start_time = time.time()
                    self.smile_duration = time.time() - self.smile_start_time
                    # (Opcional) Dibujar cuadro de la boca para debugging
                    # for (sx, sy, sw, sh) in smiles:
                    #     cv2.rectangle(roi_color, (sx, sy), (sx + sw, sy + sh), (0, 255, 255), 1)
                else:
                    self.is_smiling = False
                    self.smile_duration = 0

            # --- VERIFICACIÓN FINAL ---
            if self.blink_count >= 2 and self.smile_duration >= 2.0:
                self.fully_verified = True
                self.status_text = "VERIFICADO: ACCESO CONCEDIDO"

            # Dibujo en pantalla (UI del Video)
            color = (0, 255, 0) if self.fully_verified else (0, 255, 255)
            if "ALERTA" in self.status_text: color = (0, 0, 255)
            
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            cv2.putText(img, self.status_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return img

# Interfaz de Usuario en Streamlit
col1, col2 = st.columns([2, 1])

with col1:
    st.info("💡 Asegúrate de tener buena iluminación frontal y evita los reflejos en la cara.")
    # Usamos una clave única para el streamer para evitar conflictos
    ctx = webrtc_streamer(key="vigila-v23", video_transformer_factory=VideoProcessor)

with col2:
    st.subheader("Panel de Control")
    if ctx.video_transformer:
        st.write(f"**Estado Actual:** `{ctx.video_transformer.status_text}`")
        
        # Barra de progreso para la sonrisa
        prog_val = min(100, int((ctx.video_transformer.smile_duration / 2.0) * 100))
        st.progress(prog_val, text=f"Validación de Sonrisa Sostenida: {prog_val}%")
        
        if ctx.video_transformer.fully_verified:
            st.success("🔓 Identidad Confirmada. ¡Globos!")
            st.balloons()
        elif ctx.video_transformer.blink_count >= 2:
            st.warning("Fase 1 completada. ¡Sonríe a la cámara!")
    else:
        st.write("Esperando a que inicies la cámara...")

# Footer profesional
st.markdown("---")
st.caption("VIGILA v2.3 Friendly Edition por NCubing - Calama, Chile 2026")
