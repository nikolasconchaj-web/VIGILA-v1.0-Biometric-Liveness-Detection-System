import cv2
import time
cap = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')


blink_count = 0
is_eye_closed = False
start_time = time.time()
captcha_verified = False

print
print("Instrucciones: Parpadea 3 veces para validar que eres humano.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:

        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.putText(frame, "ESCANEANDO BIOMETRIA...", (x, y - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        roi_gray = gray[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]


        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10)


        if len(eyes) == 0:
            if not is_eye_closed:
                is_eye_closed = True
        else:
            if is_eye_closed:
                blink_count += 1
                is_eye_closed = False
                print(f"Parpadeo detectado! Total: {blink_count}")

        #
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)


    status_color = (0, 0, 255)
    status_text = f"HUMANO NO VALIDADO - Parpadeos: {blink_count}/3"

    if blink_count >= 3:
        captcha_verified = True
        status_color = (0, 255, 0)
        status_text = "VERIFICACION EXITOSA: ACCESO CONCEDIDO"


    cv2.rectangle(frame, (0, 0), (640, 50), (0, 0, 0), -1)
    cv2.putText(frame, status_text, (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)


    cv2.imshow('NC-CAPTCHA Global Security System', frame)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    if captcha_verified and (time.time() - start_time > 10):  # Damos tiempo a ver el mensaje
        print("Captcha completado con éxito. Generando Token de seguridad...")
        break

cap.release()
cv2.destroyAllWindows()