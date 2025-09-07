import cv2
import mediapipe as mp
import numpy as np

def analyze_jump(video_path=0, user_height_cm=170, show_video=True):
    """
    Detects first vertical jump after full body is visible.
    Measures jump height using shoulder displacement.

    Args:
        video_path (str|int): Path to video file or 0 for webcam.
        user_height_cm (float): Actual height of the person (cm).
        show_video (bool): Show visualization window.

    Returns:
        float: Estimated jump height in cm (None if no jump detected).
    """
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(video_path)

    shoulder_y_vals = []
    body_heights = []

    baseline_ground = None
    highest_shoulder = None
    jump_height_cm = None

    full_body_seen = False
    jump_detected = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Draw landmarks
            if show_video:
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Shoulder and ankle
            shoulder_y = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
            ankle_y = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y

            body_height_norm = ankle_y - shoulder_y
            body_heights.append(body_height_norm)

            # Step 1: Wait until body is stable (user standing still)
            if len(body_heights) > 20:  # collect 20 frames
                avg_height = np.mean(body_heights[-20:])
                var_height = np.var(body_heights[-20:])

                if avg_height > 0.4 and var_height < 0.001:  
                    full_body_seen = True
                    # Set baseline shoulder (standing ground)
                    if baseline_ground is None:
                        baseline_ground = shoulder_y
                        highest_shoulder = shoulder_y  # init with baseline

            # Step 2: After baseline, track highest shoulder
            if full_body_seen and baseline_ground is not None:
                highest_shoulder = min(highest_shoulder, shoulder_y)  # lower y = higher in frame

                # If shoulder returns near ground after reaching high point → jump done
                if shoulder_y > baseline_ground - 0.01 and highest_shoulder < baseline_ground - 0.05:
                    avg_body_norm = np.mean(body_heights)
                    scaling_factor = user_height_cm / avg_body_norm
                    jump_height_cm = (baseline_ground - highest_shoulder) * scaling_factor
                    jump_detected = True

        # Step 3: Overlay info
        if show_video:
            if not full_body_seen:
                msg = "Waiting for full body..."
            elif not jump_detected:
                msg = "Ready... Jump!"
            else:
                msg = f"Jump Height: {jump_height_cm:.2f} cm"
            cv2.putText(frame, msg, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

            cv2.imshow("Jump Analysis", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit early
                break

        if jump_detected:
            break

    cap.release()
    if show_video:
        cv2.destroyAllWindows()

    if jump_height_cm is None:
        print("⚠️ No jump detected.")
    else:
        print(f"✅ Estimated Vertical Jump Height: {jump_height_cm:.2f} cm")

    return jump_height_cm


if __name__ == "__main__":
    video_file = 0
    user_height = 169  # cm
    analyze_jump(video_file, user_height)
