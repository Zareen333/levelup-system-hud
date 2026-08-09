"""LevelUp — AI Vision Computer Vision Auto-Quest Detector Module.

Uses MediaPipe Pose Landmark Estimation to track real-world physical exercise
movements (Pushups) from webcam video frames and automatically completes quests.
"""

import math
import threading
import time

try:
    import cv2
    import mediapipe as mp
    HAS_AI_VISION = True
except ImportError:
    HAS_AI_VISION = False


class AIVisionDetector:

    def __init__(self, callback_quest_detected=None):
        self.callback = callback_quest_detected
        self.is_running = False
        self.thread = None
        self.pushup_reps = 0
        self.pushup_state = "UP"
        self.target_reps = 5
        self.last_detected_time = 0

    def start(self):
        if not HAS_AI_VISION:
            print("[AI Vision] OpenCV or MediaPipe not installed.")
            return False

        if self.is_running:
            return True

        self.is_running = True
        self.pushup_reps = 0
        self.pushup_state = "UP"
        self.thread = threading.Thread(target=self._vision_loop, daemon=True)
        self.thread.start()
        print("[AI Vision] Computer Vision landmark tracking thread started.")
        return True

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        print("[AI Vision] Computer Vision tracking stopped.")

    def _calculate_angle(self, a, b, c):
        radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
        angle = abs(radians * 180.0 / math.pi)
        if angle > 180.0:
            angle = 360.0 - angle
        return angle

    def _vision_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[AI Vision] Could not open webcam.")
            self.is_running = False
            return

        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        while self.is_running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                # Left shoulder: 11, Left elbow: 13, Left wrist: 15
                shoulder = [landmarks[11].x, landmarks[11].y]
                elbow = [landmarks[13].x, landmarks[13].y]
                wrist = [landmarks[15].x, landmarks[15].y]

                angle = self._calculate_angle(shoulder, elbow, wrist)

                if angle > 150:
                    self.pushup_state = "UP"
                elif angle < 90 and self.pushup_state == "UP":
                    self.pushup_state = "DOWN"
                elif angle > 140 and self.pushup_state == "DOWN":
                    self.pushup_state = "UP"
                    self.pushup_reps += 1
                    print(f"[AI Vision] Pushup Rep #{self.pushup_reps} Verified!")

                    if self.pushup_reps >= self.target_reps:
                        now = time.time()
                        if now - self.last_detected_time > 10.0:
                            self.last_detected_time = now
                            if self.callback:
                                self.callback("pushup")

            time.sleep(0.03)

        cap.release()
        pose.close()
