import cv2
import mediapipe as mp
import time

def analyze_punching_speed(video_path=0, hand="RIGHT", punch_threshold=0.05, reset_threshold=0.01, show=True, duration_limit=30):
    """
    Analyze punching speed from a live camera or video for a fixed duration.

    Args:
        video_path (int/str): 0 for webcam or path to .mp4 file
        hand (str): "RIGHT" or "LEFT" wrist to track
        punch_threshold (float): Speed threshold to detect punch start
        reset_threshold (float): Speed threshold to reset punch state
        show (bool): If True, displays video with overlays
        duration_limit (int): Duration (seconds) to analyze
    
    Returns:
        dict: { "total_punches": int,
                "duration_sec": float,
                "punches_per_sec": float,
                "punches_per_min": float }
    """
    # Setup mediapipe pose
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose()

    # Open video/webcam
    cap = cv2.VideoCapture(video_path)

    # Wrist to track
    wrist_index = mp_pose.PoseLandmark.LEFT_WRIST if hand.upper() == "LEFT" else mp_pose.PoseLandmark.RIGHT_WRIST

    punch_count = 0
    prev_x = None
    punching = False

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
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(img_rgb)

        if results.pose_landmarks:
            wrist = results.pose_landmarks.landmark[wrist_index]
            h, w, _ = frame.shape
            cx, cy = int(wrist.x * w), int(wrist.y * h)
            x = wrist.x  # normalized

            if prev_x is not None:
                speed = abs(x - prev_x)

                if speed > punch_threshold and not punching:
                    punch_count += 1
                    punching = True
                elif speed < reset_threshold:
                    punching = False

            prev_x = x

            # Draw pose & wrist marker
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

        # Overlay punch count + timer
        cv2.putText(frame, f"Punches: {punch_count}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        cv2.putText(frame, f"Time: {int(elapsed_time)}s/{duration_limit}s", (30, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        if show:
            cv2.imshow("Punch Analysis", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

    return {
        "total_punches": punch_count,
        "duration_sec": min(elapsed_time, duration_limit),
        "punches_per_sec": punch_count / elapsed_time if elapsed_time > 0 else 0,
        "punches_per_min": (punch_count / elapsed_time * 60) if elapsed_time > 0 else 0
    }


# Example usage (webcam, 30 seconds)
result = analyze_punching_speed(video_path=0, hand="RIGHT", show=True, duration_limit=30)
print(result)
