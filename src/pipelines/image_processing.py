from PIL import ImageEnhance,Image

from config import CONTRAST_FACTOR, SHARPNESS_FACTOR, BRIGHTNESS_FACTOR
from src.noise_processing import add_noise, denoise_image, plot_full_pipeline


def process_image_for_search(image_path, noise_type=None, denoise_method='nl_means'):
    """Full processing pipeline: add noise + denoise + enhance"""
    img = Image.open(image_path)
    original = img

    # Add noise if specified
    if noise_type:
        print(f"Adding {noise_type} noise to image")
        img = add_noise(img, noise_type)


    # Denoise image
    print(f"Applying {denoise_method} denoising")
    denoised_img = denoise_image(img, denoise_method)

    # Enhance image
    print("Applying image enhancement")
    enhancer = ImageEnhance.Sharpness(denoised_img)
    enhanced_img = enhancer.enhance(SHARPNESS_FACTOR)

    enhancer = ImageEnhance.Contrast(enhanced_img)
    enhanced_img = enhancer.enhance(CONTRAST_FACTOR)

    enhancer = ImageEnhance.Brightness(enhanced_img)
    enhanced_img = enhancer.enhance(BRIGHTNESS_FACTOR)

    plot_full_pipeline(original,img, denoised_img, enhanced_img, noise_type, denoise_method, save_path="pipeline_result.png")


    return enhanced_img

