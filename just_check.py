# ==========================================================
# UNAUTHORIZED PERSON DETECTION WITH EMAIL + WHATSAPP ALERT
# ==========================================================

import cv2
import face_recognition
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

# ===================== CONFIG =====================

# -------- EMAIL CONFIG (GMAIL) --------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "yourgmail@gmail.com"
SENDER_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"
RECEIVER_EMAIL = "receiver@gmail.com"

# -------- WHATSAPP (TWILIO) --------
TWILIO_SID = "YOUR_TWILIO_SID"
TWILIO_AUTH = "YOUR_TWILIO_AUTH_TOKEN"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"   # Twilio Sandbox
TWILIO_WHATSAPP_TO = "whatsapp:+92XXXXXXXXXX"   # Your WhatsApp number

# -------- CAMERA --------
CAMERA_INDEX = 0

# =================================================


def send_email_alert():
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = "🚨 ALERT: Unauthorized Person Detected"

        body = "Security Alert!\n\nAn unauthorized person has been detected on your camera."
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("📧 Email alert sent successfully")

    except Exception as e:
        print("❌ Email Error:", e)


def send_whatsapp_alert():
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)

        client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=TWILIO_WHATSAPP_TO,
            body="🚨 SECURITY ALERT!\nUnauthorized person detected on camera."
        )

        print("📲 WhatsApp alert sent successfully")

    except Exception as e:
        print("❌ WhatsApp Error:", e)


def detect_unauthorized_person():
    video = cv2.VideoCapture(CAMERA_INDEX)
    alert_sent = False

    print("📸 Camera Started... Press Q to Exit")

    while True:
        ret, frame = video.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        if len(face_locations) > 0 and not alert_sent:
            print("🚨 Unauthorized Person Detected!")

            send_email_alert()
            send_whatsapp_alert()

            alert_sent = True
            time.sleep(10)  # spam control

        cv2.imshow("Security Camera", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()


# ===================== MAIN =====================
if __name__ == "__main__":
    detect_unauthorized_person()
