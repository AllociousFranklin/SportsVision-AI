import cv2
import mediapipe as mp
from db_utils import save_punch_result

def analyze_punching_speed(video_path, user_id=1, hand="RIGHT", punch_threshold=0.05, reset_threshold=0.01, show=True):
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose()

    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frames / fps if fps > 0 else 0

    wrist_index = mp_pose.PoseLandmark.LEFT_WRIST if hand.upper() == "LEFT" else mp_pose.PoseLandmark.RIGHT_WRIST

    punch_count, prev_x, punching = 0, None, False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(img_rgb)

        if results.pose_landmarks:
            wrist = results.pose_landmarks.landmark[wrist_index]
            h, w, _ = frame.shape
            cx, cy = int(wrist.x * w), int(wrist.y * h)
            x = wrist.x

            if prev_x is not None:
                speed = abs(x - prev_x)
                if speed > punch_threshold and not punching:
                    punch_count += 1
                    punching = True
                elif speed < reset_threshold:
                    punching = False
            prev_x = x

            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

        if show:
            cv2.putText(frame, f"Punches: {punch_count}", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.imshow("Punch Analysis", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    if show:
        cv2.destroyAllWindows()

    punches_per_sec = punch_count / duration if duration > 0 else 0
    punches_per_min = punches_per_sec * 60 if duration > 0 else 0

    result = {
        "total_punches": punch_count,
        "duration_sec": duration,
        "punches_per_sec": punches_per_sec,
        "punches_per_min": punches_per_min
    }

    print("✅ Punch Analysis:", result)
    save_punch_result(user_id, video_path, punch_count, duration, punches_per_sec, punches_per_min)
    return result

