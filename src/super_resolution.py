

import os
import cv2
import torch
from basicsr.archs.srvgg_arch import SRVGGNetCompact
from gfpgan.utils import GFPGANer
from realesrgan.utils import RealESRGANer

def enhance_face_with_gfpgan_v14(
        img_path: str,
        output_path: str = None,
        upscaling_factor: int = 2
) -> torch.Tensor:
    """
    Load GFPGAN v1.4 + RealESRGAN background upsampler, then restore/enhance the face(s)
    in `img_path`. Returns a torch.Tensor (H×W×3, RGB) of the restored image.
    If `output_path` is provided, also saves the result there.

    Args:
        img_path (str): Path to the input image (e.g., "input.jpg").
        output_path (str, optional): Where to save the output. If None, no file is written.
        upscaling_factor (int, default=2): Final rescaling factor for the entire image
            (after face restoration). Must be ≥1. If >2, the code will clamp to 2.

    Returns:
        torch.Tensor: Restored image as an RGB tensor (dtype=torch.uint8).
    """


    gfpgan_url = (
        "https://github.com/TencentARC/GFPGAN/"
        "releases/download/v1.3.0/GFPGANv1.4.pth"
    )
    gfpgan_ckpt = "GFPGANv1.4.pth"

    # RealESRGAN ×4 (general) weights
    real_esrgan_url = (
        "https://github.com/xinntao/Real-ESRGAN/"
        "releases/download/v0.2.5.0/realesr-general-x4v3.pth"
    )
    real_esrgan_ckpt = "realesr-general-x4v3.pth"

    if not os.path.isfile(gfpgan_ckpt):
        print(f"[INFO] Downloading {gfpgan_ckpt} ...")
        torch.hub.download_url_to_file(gfpgan_url, gfpgan_ckpt)

    if not os.path.isfile(real_esrgan_ckpt):
        print(f"[INFO] Downloading {real_esrgan_ckpt} ...")
        torch.hub.download_url_to_file(real_esrgan_url, real_esrgan_ckpt)

    
    bsrvgg = SRVGGNetCompact(
        num_in_ch=3, num_out_ch=3, num_feat=64,
        num_conv=32, upscale=4, act_type="prelu"
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    half = True if (device == "cuda") else False

    upsampler = RealESRGANer(
        scale=4,
        model_path=real_esrgan_ckpt,
        model=bsrvgg,
        tile=1,          
        tile_pad=10,
        pre_pad=0,
        half=half      
    )

    
    face_enhancer = GFPGANer(
        model_path=gfpgan_ckpt,
        upscale=2,
        arch="clean",           
        channel_multiplier=2,
        bg_upsampler=upsampler    
    )


    img_bgr = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img_bgr is None:
        raise FileNotFoundError(f"Cannot read image at '{img_path}'")

    # Handle α-channel if present
    if len(img_bgr.shape) == 3 and img_bgr.shape[2] == 4:
        img_mode = "RGBA"
        bgr = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2BGR)
    elif len(img_bgr.shape) == 2:
        img_mode = None
        bgr = cv2.cvtColor(img_bgr, cv2.COLOR_GRAY2BGR)
    else:
        img_mode = None
        bgr = img_bgr

    # Prevent extremely large images
    H, W = bgr.shape[:2]
    if H > 3500 or W > 3500:
        raise ValueError("Input image is too large (>3500px in either dimension).")

    if H < 300 or W < 300:
        bgr = cv2.resize(
            bgr,
            (W * 2, H * 2),
            interpolation=cv2.INTER_LANCZOS4
        )


    _, _, restored_bgr = face_enhancer.enhance(
        bgr,             
        has_aligned=False,
        only_center_face=False,
        paste_back=True
    )


    final_scale = min(upscaling_factor, 2)
    if final_scale != 2:
        interp = (
            cv2.INTER_AREA if final_scale < 2 else cv2.INTER_LANCZOS4
        )
        h2, w2 = restored_bgr.shape[:2]
        new_w = int(w2 * final_scale / 2)
        new_h = int(h2 * final_scale / 2)
        if new_w > 0 and new_h > 0:
            restored_bgr = cv2.resize(restored_bgr, (new_w, new_h), interpolation=interp)

    ext = "png" if (img_mode == "RGBA") else "jpg"

    # Convert BGR→RGB for returning to caller
    restored_rgb = cv2.cvtColor(restored_bgr, cv2.COLOR_BGR2RGB)

    if output_path is not None:
        out_dir = os.path.dirname(output_path)
        if len(out_dir) > 0 and not os.path.isdir(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        base, given_ext = os.path.splitext(output_path)
        if given_ext.lower() not in [".jpg", ".jpeg", ".png"]:
            output_path = f"{base}.{ext}"

        # Convert RGB→BGR again for OpenCV save
        save_bgr = cv2.cvtColor(restored_rgb, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, save_bgr)
        print(f"[INFO] Saved restored image to '{output_path}'")

    return torch.from_numpy(restored_rgb)

