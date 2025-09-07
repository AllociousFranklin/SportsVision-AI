import cv2
import mediapipe as mp
from db_utils import save_pushup_result

def analyze_pushups(video_path, user_id=1, show_video=True):
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(video_path)
    counter = 0
    stage = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            shoulder_y = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
            elbow_y = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y

            if shoulder_y > elbow_y:
                stage = "down"
            if shoulder_y < elbow_y and stage == "down":
                stage = "up"
                counter += 1

            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        if show_video:
            cv2.putText(frame, f'Push-ups: {counter}', (30, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            cv2.imshow("Push-up Counter", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    if show_video:
        cv2.destroyAllWindows()

    print(f"✅ Total Push-ups: {counter}")
    save_pushup_result(user_id, video_path, counter)
    return counter

