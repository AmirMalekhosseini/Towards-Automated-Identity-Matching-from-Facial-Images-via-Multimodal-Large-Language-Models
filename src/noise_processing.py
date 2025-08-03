import cv2
import numpy as np
from PIL import Image, ImageFilter
from matplotlib import pyplot as plt


def add_gaussian_noise(image, mean=0, sigma=25):
    img_array = np.array(image)
    noise = np.random.normal(mean, sigma, img_array.shape).astype(np.uint8)
    noisy_array = cv2.add(img_array, noise)
    return Image.fromarray(noisy_array)


def add_salt_pepper_noise(image, salt_prob=0.01, pepper_prob=0.01):

    img_array = np.array(image)
    noisy_array = np.copy(img_array)

    # Salt noise
    salt_mask = np.random.random(img_array.shape[:2]) < salt_prob
    noisy_array[salt_mask] = 255

    # Pepper noise
    pepper_mask = np.random.random(img_array.shape[:2]) < pepper_prob
    noisy_array[pepper_mask] = 0

    return Image.fromarray(noisy_array)


def add_noise(image, noise_type='gaussian', **kwargs):

    if noise_type == 'gaussian':
        return add_gaussian_noise(image, **kwargs)
    elif noise_type == 'salt_pepper':
        return add_salt_pepper_noise(image, **kwargs)
    elif noise_type == 'poisson':
        img_array = np.array(image)
        noisy_array = np.random.poisson(img_array).astype(np.uint8)
        return Image.fromarray(noisy_array)
    else:
        raise ValueError(f"Unsupported noise type: {noise_type}")

def denoise_median(image, size=3):

    return image.filter(ImageFilter.MedianFilter(size))

def denoise_gaussian(image, radius=2):

    return image.filter(ImageFilter.GaussianBlur(radius))

def denoise_bilateral(image, d=9, sigma_color=75, sigma_space=75):

    img_array = np.array(image)
    denoised_array = cv2.bilateralFilter(img_array, d, sigma_color, sigma_space)
    return Image.fromarray(denoised_array)

def denoise_nl_means(image, h=10, template_size=7, search_size=21):

    img_array = np.array(image)
    if img_array.shape[2] == 4:
        bgr_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
        denoised_array = cv2.fastNlMeansDenoisingColored(bgr_array, None, h, h, template_size, search_size)
        denoised_array = cv2.cvtColor(denoised_array, cv2.COLOR_BGRA2RGBA)
    else:
        bgr_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        denoised_array = cv2.fastNlMeansDenoisingColored(bgr_array, None, h, h, template_size, search_size)
        denoised_array = cv2.cvtColor(denoised_array, cv2.COLOR_BGR2RGB)
    return Image.fromarray(denoised_array)

def denoise_image(image, method='nl_means', **kwargs):

    if method == 'median':
        return denoise_median(image, **kwargs)
    elif method == 'gaussian':
        return denoise_gaussian(image, **kwargs)
    elif method == 'bilateral':
        return denoise_bilateral(image, **kwargs)
    elif method == 'nl_means':
        return denoise_nl_means(image, **kwargs)
    else:
        raise ValueError(f"Unsupported denoise method: {method}")


def plot_full_pipeline(original, noisy, denoised, enhanced, noise_type, denoise_method, save_path="full_comparison.png"):
    """Display and save original, noisy, denoised, and enhanced images side by side."""
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    titles = [
        "Original Image",
        f"Noisy Image ({noise_type})",
        f"Denoised Image ({denoise_method})",
        "Enhanced Image"
    ]
    images = [original, noisy, denoised, enhanced]

    for ax, img, title in zip(axes, images, titles):
        ax.imshow(img)
        ax.set_title(title)
        ax.axis("off")

    plt.tight_layout()
    plt.savefig('enhanced_images_output.png', bbox_inches='tight')
    print(f"Plot saved to: {save_path}")
    plt.show()