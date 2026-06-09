from ultralytics import YOLO
import cv2
import numpy as np

_model = None

def get_model():
    global _model
    if _model is None:
        _model = YOLO("yolov8n-pose.pt")
    return _model

class PoseEstimator:
    def __init__(self):
        self.model = get_model()
        self.skeleton = [
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
            (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16)
        ]

    def get_keypoints(self, img):
        h, w = img.shape[:2]
        scale = 256 / max(h, w)
        small = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

        results = self.model(small, imgsz=256, verbose=False, conf=0.3)
        if not results or len(results[0].keypoints) == 0:
            return None, None

        kpts = results[0].keypoints.xy[0].cpu().numpy() / scale
        conf = results[0].keypoints.conf[0].cpu().numpy()
        if np.mean(conf) < 0.3:
            return None, None

        return kpts, (0, 0, w, h)

    def draw_skeleton(self, img, keypoints, line_colors=None):
        if keypoints is None:
            return img
        for i, j in self.skeleton:
            if i >= len(keypoints) or j >= len(keypoints):
                continue
            x1, y1 = keypoints[i].astype(int)
            x2, y2 = keypoints[j].astype(int)
            if x1 <= 0 or y1 <= 0 or x2 <= 0 or y2 <= 0:
                continue
            color = line_colors.get((i, j), (255, 255, 255)) if line_colors else (255, 255, 255)
            cv2.line(img, (x1, y1), (x2, y2), color, 2)
        return img

    def draw_text(self, img, text, pos, font_scale=0.7, color=(0, 255, 255)):
        cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)
        return img
