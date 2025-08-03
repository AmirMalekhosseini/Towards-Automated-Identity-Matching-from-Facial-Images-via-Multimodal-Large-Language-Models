import glob
import os
import re
import shutil
import time

import requests
from urllib.parse import urlparse, unquote
import urllib3
from selenium.common import ElementNotInteractableException
from selenium.webdriver.common.by import By

from config import DOWNLOAD_VERIFY_SSL, CLIENT_ID
import json


def sanitize_filename(text_to_sanitize):
    """Creates a safe filename."""
    name_part = str(text_to_sanitize)
    if "http" in name_part and not os.path.exists(name_part):
        try:
            parsed_url = urlparse(name_part)
            name_part = os.path.basename(unquote(parsed_url.path))
            if not name_part and parsed_url.netloc:  
                name_part = parsed_url.netloc
            elif not name_part:  # Ultimate fallback
                name_part = "downloaded_image"
        except Exception:
            name_part = "downloaded_image"  

    name = re.sub(r'[\\/*?:"<>|]', "_", name_part)
    name = re.sub(r'\s+', '_', name)
    name = (name[:100]) if len(name) > 100 else name  # Limit length
    name = name.strip('_.- ')
    if not name:
        name = "unknown_image"
    return name


def download_image(image_url, save_path, verify_ssl=DOWNLOAD_VERIFY_SSL):
    """Downloads an image from a URL and saves it to save_path."""
    try:
        print(f"Downloading input image from: {image_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

        if not verify_ssl:
            print(
                "WARNING: SSL certificate verification is DISABLED for this download. This can be insecure.")
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.get(image_url, stream=True,
                                timeout=30, headers=headers, verify=verify_ssl)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Input image downloaded successfully to: {save_path}")
        return save_path
    except requests.exceptions.SSLError as e:
        print(f"SSL Error downloading image {image_url}: {e}")
        if verify_ssl:
            print("You can try setting DOWNLOAD_VERIFY_SSL = False at the top of the script to bypass this (at your own risk).")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image {image_url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during image download: {e}")
        return None


def clear_folder_contents(folder_path):
    """Removes all files and subdirectories within a given folder."""
    if os.path.exists(folder_path):
        print(f"Clearing contents of: {folder_path}")
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                print(f"Removed: {item_path}")
            except Exception as e:
                print(f"Error removing {item_path}: {e}")
    else:
        print(f"Folder not found: {folder_path}")


def handle_popups(driver):
    """
    Finds and clicks pop-up buttons in multiple attempts to clear the screen.
    Handles cookie consents, login modals, and other overlays.
    """
    print("Starting advanced pop-up handling...")
    # Try up to 3 times to find and close pop-ups. This handles chained modals.
    for i in range(3):
        found_and_clicked_in_iteration = False

        # A dictionary of selectors, from most specific to most generic
        selectors = {
            "LinkedIn Login 'X' button": "//button[contains(@class, 'modal__dismiss')]",
            "Element with aria-label 'Close' or 'Dismiss'": "//*[@aria-label='Close' or @aria-label='close' or @aria-label='Dismiss' or @aria-label='dismiss']",
            "Button with text 'accept all'": "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
            "Button with text 'accept'": "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
            "Button with text 'agree'": "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
            "Button with text 'consent'": "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'consent')]",
            "Button with text 'close'": "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'close')]",
        }

        for name, xpath in selectors.items():
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        print(
                            f"  - Found clickable pop-up element: '{name}'. Clicking it.")
                        try:
                            element.click()
                        except ElementNotInteractableException:
                            # If standard click is blocked, use JavaScript
                            print(
                                "    - Element not directly clickable, trying JavaScript click.")
                            driver.execute_script(
                                "arguments[0].click();", element)

                        found_and_clicked_in_iteration = True
                        print("    - Click successful. Waiting for page to update...")
                        time.sleep(2.5)  # Wait for UI to settle
                        break  # Exit the inner 'element' loop
            except Exception as e:
                print(
                    f"    - An error occurred while searching for '{name}': {e}")

            if found_and_clicked_in_iteration:
                break  

        if not found_and_clicked_in_iteration:
            print("  - No more clickable pop-ups found. Proceeding with screenshot.")
            break  

    print("Finished pop-up handling.")

def upload_image_to_imgur(image_path: str) -> str:
    """
    Uploads a local image to Imgur and returns the image URL.

    Parameters:
        image_path (str): The file path to the local image.
        client_id (str): Your Imgur API Client ID.

    Returns:
        str: The URL of the uploaded image.

    Raises:
        Exception: If the upload fails or the response is invalid.
    """
    headers = {'Authorization': f'Client-ID {CLIENT_ID}'}
    with open(image_path, 'rb') as image_file:
        files = {'image': image_file}
        response = requests.post('https://api.imgur.com/3/image', headers=headers, files=files)

    if response.status_code == 200:
        return response.json()['data']['link']
    else:
        raise Exception(f"Image upload failed with status code {response.status_code}: {response.text}")


def upload_image_to_imgbb(image_path: str) -> str:
    """
    Uploads a local image to ImgBB and returns the direct image URL.

    Parameters:
        image_path (str): Path to the image file.
        api_key (str): Your ImgBB API key.

    Returns:
        str: URL of the uploaded image.

    Raises:
        Exception: If upload fails.
    """
    with open(image_path, "rb") as img_file:
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={'key': 'dfac5225c08c99ea4db6511c2ae1ff3e'},
            files={'image': img_file}
        )

    if response.status_code == 200:
        data = response.json().get('data', {})
        return data.get('display_url') or data.get('url')
    else:
        raise Exception(f"ImgBB upload failed {response.status_code}: {response.text}")

def save_people_data(data, filepath="people_data.json"):
    """Saves data to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filepath}")


def add_person_and_results(data, name_or_image_path, search_results):
    """Adds a new person/image entry with search results to the data."""
    new_entry = {
        "identifier": name_or_image_path,
        "search_results": search_results  
    }
    data.append(new_entry)
    print(f"Added entry for: {name_or_image_path}")

def process_new_json_files(
        source_dir: str = 'reverse_image_search_results_new/',
        output_path: str = 'reverse_image_search_results_new/'
):

    grouped = {}

    # Find all per-face JSON files
    pattern = os.path.join(source_dir, 'results_*.json')
    for filepath in glob.glob(pattern):
        filename = os.path.basename(filepath)
        # e.g. 'results_3_0.json' -> identifier '3'
        try:
            _, identifier, _ = filename.split('_', 2)
        except ValueError:
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            hits = json.load(f)

        grouped.setdefault(identifier, []).extend(hits)

    output_list = []
    for identifier, hits in grouped.items():
        output_list.append({
            "identifier": identifier,
            "search_results": {
                "image_results": hits
            }
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_list, f, indent=4)

    print(f"Aggregated {len(output_list)} identifiers into '{output_path}'")