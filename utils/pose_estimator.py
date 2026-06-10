from ultralytics import YOLO
import cv2
import numpy as np

_model = None

def get_model():
global _model
if _model is None:
_model = YOLO(“yolov8n-pose.pt”)
return _model

class PoseEstimator:
def **init**(self, skip_frames=2):
“””
Optimized PoseEstimator for faster inference

```
    Args:
        skip_frames: Process every nth frame (2 = 50% inference load)
    """
    self.model = get_model()
    self.skeleton = [
        (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
        (5, 11), (6, 12), (11, 12),
        (11, 13), (13, 15), (12, 14), (14, 16)
    ]
    self.skip_frames = skip_frames
    self.frame_count = 0
    self.last_keypoints = None
    self.last_bbox = None
    
def get_keypoints(self, img):
    """
    Get keypoints with frame skipping for speed.
    Returns cached keypoints on skipped frames.
    """
    self.frame_count += 1
    
    # Skip frames to reduce computation load
    if self.frame_count % self.skip_frames != 0:
        return self.last_keypoints, self.last_bbox
    
    h, w = img.shape[:2]
    
    # Smaller input = faster inference (192 vs 256)
    scale = 192 / max(h, w)
    small = cv2.resize(img, (int(w * scale), int(h * scale)), 
                      interpolation=cv2.INTER_LINEAR)

    # Faster inference with optimized settings
    results = self.model(small, imgsz=192, verbose=False, conf=0.25)
    
    if not results or len(results[0].keypoints) == 0:
        return self.last_keypoints, self.last_bbox

    kpts = results[0].keypoints.xy[0].cpu().numpy() / scale
    conf = results[0].keypoints.conf[0].cpu().numpy()
    
    # Lower confidence threshold for better tolerance
    if np.mean(conf) < 0.25:
        return self.last_keypoints, self.last_bbox

    self.last_keypoints = kpts
    self.last_bbox = (0, 0, w, h)
    return kpts, (0, 0, w, h)

def draw_skeleton(self, img, keypoints, line_colors=None):
    """Draw skeleton joints and connections"""
    if keypoints is None:
        return img
    
    for i, j in self.skeleton:
        if i >= len(keypoints) or j >= len(keypoints):
            continue
        
        x1, y1 = keypoints[i].astype(int)
        x2, y2 = keypoints[j].astype(int)
        
        # Skip invalid points
        if x1 <= 0 or y1 <= 0 or x2 <= 0 or y2 <= 0:
            continue
        
        color = line_colors.get((i, j), (255, 255, 255)) if line_colors else (255, 255, 255)
        cv2.line(img, (x1, y1), (x2, y2), color, 2)
    
    return img

def draw_text(self, img, text, pos, font_scale=0.7, color=(0, 255, 255)):
    """Draw text on frame"""
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)
    return img
```
