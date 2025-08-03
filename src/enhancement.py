import os
import tempfile
import cv2
import numpy as np
from PIL import Image
from rembg import remove
from facenet_pytorch import MTCNN
import torch

def remove_background_deeplearning(orig_bgr: np.ndarray) -> np.ndarray:
    """Uses rembg to remove the background, returning a BGR image with a black background."""
    orig_rgb = cv2.cvtColor(orig_bgr, cv2.COLOR_BGR2RGB)
    pil_rgb = Image.fromarray(orig_rgb)
    fg_rgba = remove(pil_rgb)
    black_bg = Image.new("RGBA", fg_rgba.size, (0, 0, 0, 255))
    composited = Image.alpha_composite(black_bg, fg_rgba)
    composited_rgb = composited.convert("RGB")
    fg_bgr = cv2.cvtColor(np.array(composited_rgb), cv2.COLOR_RGB2BGR)
    return fg_bgr

def detect_foreground_faces_dl_bg_removal(
        image_path: str,
        save_folder: str = "faces_foreground_dl",
        expand_ratio_w: float = 0.5,
        expand_ratio_h: float = 1.0,
        black_thresh_ratio: float = 0.7
) -> list:
    """
    Detects foreground faces using a PyTorch-based MTCNN model after background removal.
    """
    os.makedirs(save_folder, exist_ok=True)

    orig_bgr = cv2.imread(image_path)
    if orig_bgr is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")
    img_h, img_w = orig_bgr.shape[:2]

    # Use rembg to get an image with the background turned to black
    fg_bgr = remove_background_deeplearning(orig_bgr)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    mtcnn = MTCNN(keep_all=True, device=device)

    img_rgb = cv2.cvtColor(orig_bgr, cv2.COLOR_BGR2RGB)
    
    boxes, _ = mtcnn.detect(img_rgb)

    face_crops = []
    if boxes is not None:
        for idx, box in enumerate(boxes):
            x1, y1, x2, y2 = [int(coord) for coord in box]
            w = x2 - x1
            h = y2 - y1

            x_exp = int(w * expand_ratio_w)
            y_exp = int(h * expand_ratio_h)
            x1e = max(x1 - x_exp, 0)
            y1e = max(y1 - y_exp, 0)
            x2e = min(x2 + x_exp, img_w)
            y2e = min(y2 + y_exp, img_h)

            # Check the "foreground only" image to see if the face is in the background
            fg_crop = fg_bgr[y1e:y2e, x1e:x2e]
            if fg_crop.size == 0:
                continue
            
            gray_crop = cv2.cvtColor(fg_crop, cv2.COLOR_BGR2GRAY)
            total_pixels = gray_crop.size
            black_pixels = int(np.count_nonzero(gray_crop == 0))
            
            if black_pixels / float(total_pixels) > black_thresh_ratio:
                # Too much black in the region, likely a background face, so we skip it.
                continue

            # If it's a foreground face, crop it from the ORIGINAL color image
            orig_crop = orig_bgr[y1e:y2e, x1e:x2e]
            face_crops.append(orig_crop)
    else:
        print("No faces detected.")

    return face_crops