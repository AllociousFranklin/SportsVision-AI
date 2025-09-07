import cv2
import mediapipe as mp
import time

def analyze_pushups(video_path=0, show_video=True, duration_limit=30):
    """
    Analyze push-ups from a webcam or video for a fixed duration.

    Args:
        video_path (int/str): 0 for webcam or path to video file.
        show_video (bool): If True, display the video with overlay.
        duration_limit (int): Duration (seconds) to analyze.

    Returns:
        dict: {
            "total_pushups": int,
            "duration_sec": float,
            "pushups_per_sec": float,
            "pushups_per_min": float
        }
    """
    # Initialize MediaPipe pose
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    # Video capture
    cap = cv2.VideoCapture(video_path)
    counter = 0
    stage = None  # "down" or "up"

    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Stop after duration_limit seconds
        elapsed_time = time.time() - start_time
        if elapsed_time >= duration_limit:
            break

        # Convert to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)

        # Convert back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Get coordinates of left shoulder and elbow
            shoulder_y = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
            elbow_y = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y

            # Push-up logic
            if shoulder_y > elbow_y:
                stage = "down"
            if shoulder_y < elbow_y and stage == "down":
                stage = "up"
                counter += 1

            # Draw pose landmarks
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Overlay push-up count and timer
        cv2.putText(image, f'Push-ups: {counter}', (30, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv2.LINE_AA)
        cv2.putText(image, f"Time: {int(elapsed_time)}s/{duration_limit}s", (30, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        if show_video:
            cv2.imshow("Push-up Counter", image)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    if show_video:
        cv2.destroyAllWindows()

    duration = min(elapsed_time, duration_limit)
    result = {
        "total_pushups": counter,
        "duration_sec": duration,
        "pushups_per_sec": counter / duration if duration > 0 else 0,
        "pushups_per_min": (counter / duration * 60) if duration > 0 else 0
    }

    print(f"✅ Total Push-ups: {counter} in {int(duration)}s")
    return result


# Example usage (webcam for 30s)
result = analyze_pushups(video_path=0, show_video=True, duration_limit=30)
print(result)
