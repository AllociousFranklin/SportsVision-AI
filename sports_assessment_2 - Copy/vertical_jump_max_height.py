import cv2
import mediapipe as mp
import numpy as np
from db_utils import save_jump_result

def analyze_jump(video_path, user_height_cm=170, user_id=1, show_video=True):
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(video_path)
    shoulder_positions, body_heights = [], []
    ground, apex = None, None
    jump_cm = 0.0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            shoulder_y = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
            ankle_y = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y

            shoulder_positions.append(shoulder_y)
            body_heights.append(ankle_y - shoulder_y)

            ground = max(shoulder_positions)
            apex = min(shoulder_positions)
            jump_norm = ground - apex
            avg_body_norm = np.mean(body_heights) if body_heights else 1
            scaling_factor = user_height_cm / avg_body_norm
            jump_cm = jump_norm * scaling_factor - user_height_cm

            if show_video:
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                cv2.putText(frame, f"Jump Height: {jump_cm:.2f} cm", (30, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        if show_video:
            cv2.imshow("Jump Analysis", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    cap.release()
    if show_video:
        cv2.destroyAllWindows()

    print(f"✅ Vertical Jump Height: {abs(jump_cm):.2f} cm")
    save_jump_result(user_id, video_path, abs(jump_cm))
    return abs(jump_cm)

