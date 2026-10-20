import cv2
import mediapipe as mp
import time
from pynput.mouse import Controller, Button
import pyautogui
from collections import deque
import numpy as np  # For the gaze tracker window

# Setup
cam = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
mouse = Controller()
screen_w, screen_h = pyautogui.size()

# Blink detection timing
blink_start_time = None
last_click_time = 0
single_click_min = 0.1
single_click_max = 0.35
double_click_gap = 0.6
long_blink_min = 0.4

# Cursor smoothing and calibration
position_history = deque(maxlen=5)
movement_multiplier = 2.0
neutral_x = None
neutral_y = None

def detect_blink(landmarks, frame_h):
    """Measure vertical eye distance to detect blinks."""
    upper = landmarks[159].y * frame_h
    lower = landmarks[145].y * frame_h
    return abs(upper - lower)

def smooth_cursor(x, y):
    position_history.append((x, y))
    avg_x = sum(p[0] for p in position_history) / len(position_history)
    avg_y = sum(p[1] for p in position_history) / len(position_history)
    return int(avg_x), int(avg_y)

print("👁️ Eye Mouse Started... Press 'q' to exit.")

while True:
    success, frame = cam.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output = face_mesh.process(rgb)
    h, w, _ = frame.shape

    if output.multi_face_landmarks:
        landmarks = output.multi_face_landmarks[0].landmark

        # Get iris center
        iris_x = landmarks[474].x
        iris_y = landmarks[474].y

        # Calibrate neutral gaze center
        if neutral_x is None:
            neutral_x = iris_x
            neutral_y = iris_y

        # Calculate deltas
        dx = (iris_x - neutral_x) * movement_multiplier
        dy = (iris_y - neutral_y) * movement_multiplier

        # Map to screen coordinates
        screen_x = int(screen_w / 2 + screen_w * dx)
        screen_y = int(screen_h / 2 + screen_h * dy)

        # Smooth cursor
        smoothed_x, smoothed_y = smooth_cursor(screen_x, screen_y)
        mouse.position = (smoothed_x, smoothed_y)

        # ---- VISUALIZATION ----
        # Draw iris dot on webcam image
        iris_px = int(iris_x * w)
        iris_py = int(iris_y * h)
        cv2.circle(frame, (iris_px, iris_py), 5, (0, 255, 255), -1)  # Yellow dot on iris

        # Dot for where the screen position maps (optional)
        mapped_x = smoothed_x * w // screen_w
        mapped_y = smoothed_y * h // screen_h
        cv2.circle(frame, (mapped_x, mapped_y), 5, (255, 0, 0), -1)  # Blue dot for screen mapped

        # ---- GAZE TRACKER WINDOW ----
        gaze_vis = 255 * np.ones((screen_h // 4, screen_w // 4, 3), dtype=np.uint8)
        gaze_dot_x = smoothed_x // 4
        gaze_dot_y = smoothed_y // 4
        cv2.circle(gaze_vis, (gaze_dot_x, gaze_dot_y), 10, (0, 0, 255), -1)  # Red dot

        # ---- BLINK DETECTION ----
        eye_dist = detect_blink(landmarks, h)
        if eye_dist < 5:
            if blink_start_time is None:
                blink_start_time = time.time()
        else:
            if blink_start_time:
                blink_duration = time.time() - blink_start_time
                blink_start_time = None
                now = time.time()

                if single_click_min <= blink_duration <= single_click_max:
                    if now - last_click_time <= double_click_gap:
                        print("🖱️ Double Click")
                        mouse.click(Button.left, 2)
                    else:
                        print("🖱️ Single Click")
                        mouse.click(Button.left, 1)
                    last_click_time = now
                elif blink_duration >= long_blink_min:
                    print("🖱️ Long Blink (Double Click)")
                    mouse.click(Button.left, 2)
                    last_click_time = now

    # Show the webcam with overlays
    cv2.imshow("Eye Controlled Mouse", frame)

    # Show gaze tracker
    cv2.imshow("Gaze Tracker", gaze_vis)

    # Quit with 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
