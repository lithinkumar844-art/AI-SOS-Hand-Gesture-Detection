import cv2
import mediapipe as mp
import time
import pyttsx3
import sys
import smtplib
import pywhatkit as kit
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
if sys.platform.startswith("win"):
    import winsound
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.6)
cap = cv2.VideoCapture(0)
engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)
gesture_response = {
    "FIVE": "Stop!",
    "FIST": "Ready!",
    "PEACE": "Peace!",
    "THUMBS_UP": "Good job!",
    "ONE": "One finger. Attention!",
    "OK": "Okay! All good.",
    "CALL_ME": "Call me!",
    "LOVE": "I love you!",
    "SOS": "Emergency! Please help me!",
}
def speak(text):
    engine.say(text)
    engine.runAndWait()
def alarm():
    if sys.platform.startswith("win"):
        for _ in range(3):
            winsound.Beep(1000, 500)
    else:
        print("\a")
def get_location():
    try:
        res = requests.get('https://ipinfo.io')
        data = res.json()
        loc = data.get('loc', '')
        city = data.get('city', '')
        region = data.get('region', '')
        country = data.get('country', '')
        google_maps_link = f"https://www.google.com/maps?q={loc}" if loc else "Location not found"
        return f"{city}, {region}, {country}\n{google_maps_link}"
    except:
        return "Location not available"
def send_email_alert():
    sender = "your_email@gmail.com"
    password = "your_app_password"
    receiver = "receiver_email@gmail.com"
    location_info = get_location()
    subject = " SOS Alert!"
    body = f"Emergency! SOS gesture detected.\n\nApproximate Location:\n{location_info}"
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        server = smtplib.SMTP("lithinkumar844@gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        print(" SOS Email sent!")
    except Exception as e:
        print(" Email failed:", e)
def send_whatsapp_alert():
    location_info = get_location()
    try:
        phone = "+918220455767"
        message = f" SOS Alert! Emergency detected.\nApproximate Location:\n{location_info}"
        kit.sendwhatmsg_instantly(phone, message, 15, True, 2)
        print(" WhatsApp alert sent!")
    except Exception as e:
        print(" WhatsApp failed:", e)
def classify_gesture(landmarks):
    index_up = landmarks[8].y < landmarks[6].y
    middle_up = landmarks[12].y < landmarks[10].y
    ring_up = landmarks[16].y < landmarks[14].y
    pinky_up = landmarks[20].y < landmarks[18].y
    thumb_up = landmarks[4].y < landmarks[2].y

    if index_up and middle_up and ring_up and pinky_up and thumb_up:
        return "SOS"
    if not index_up and not middle_up and not ring_up and not pinky_up and not thumb_up:
        return "FIST"
    if index_up and not middle_up and not ring_up and not pinky_up and not thumb_up:
        return "ONE"
    if index_up and middle_up and not ring_up and not pinky_up:
        return "PEACE"
    if thumb_up and not index_up and not middle_up and not ring_up and not pinky_up:
        return "THUMBS_UP"
    if abs(landmarks[8].x - landmarks[4].x) < 0.05 and abs(landmarks[8].y - landmarks[4].y) < 0.05:
        if middle_up and ring_up and pinky_up:
            return "OK"
    if thumb_up and not index_up and not middle_up and not ring_up and pinky_up:
        return "CALL_ME"
    if index_up and pinky_up and thumb_up and not middle_up and not ring_up:
        return "LOVE"
    return None
last_spoken_time = 0
speak_cooldown = 3
sos_frame_count = 0
sos_trigger_frames = 5 
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    gesture = None
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            landmarks = hand_landmarks.landmark
            gesture = classify_gesture(landmarks)
            break
    current_time = time.time()
    if gesture == "SOS":
        sos_frame_count += 1
    else:
        sos_frame_count = 0
    if sos_frame_count >= sos_trigger_frames:
        if current_time - last_spoken_time > speak_cooldown:
            speak(gesture_response["SOS"])
            alarm()
            send_email_alert()
            send_whatsapp_alert()
            last_spoken_time = current_time
            sos_frame_count = 0
    if gesture and gesture != "SOS":
        cv2.putText(frame, gesture_response[gesture], (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        if current_time - last_spoken_time > speak_cooldown:
            speak(gesture_response[gesture])
            last_spoken_time = current_time
    cv2.putText(frame, "Press Q to Quit", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.imshow("Hand Sign Scanner with Reliable SOS", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()