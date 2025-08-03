import shutil
from config import VIEWPORT_WIDTH, VIEWPORT_HEIGHT, OVERLAP_PIXELS, SKIP_DOMAINS, BASE_OUTPUT_DIR_FOR_ALL_SEARCHES
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from src.utils import handle_popups


import os
import json
import re
from collections import defaultdict


NEW_FILES_DIR = 'reverse_image_search_results_new/'

NEW_DATA_OUTPUT_PATH = 'newly_processed_results.json'


def process_new_json_files():
    """
    Finds new result files, formats them according to specific rules,
    and saves them into a new, single JSON file.
    """
    new_data = []

    file_pattern = re.compile(r"results_(\d+)_(\d+)\.json")
    file_groups = defaultdict(list)

    print(f"\n🔎 Scanning for new files in '{NEW_FILES_DIR}'...")
    if not os.path.isdir(NEW_FILES_DIR):
        print(
            f" Error: Directory not found at '{NEW_FILES_DIR}'. Please create it and add your files."
        )
        return

    for filename in sorted(os.listdir(NEW_FILES_DIR)):
        match = file_pattern.match(filename)
        if match:
            base_number = match.group(1)
            file_groups[base_number].append(filename)

    total_new_files = sum(len(v) for v in file_groups.values())
    if total_new_files == 0:
        print("No new result files found to process.")
        return

    print(
        f"Found {total_new_files} new files to process, grouped into {len(file_groups)} unique images."
    )

    for base_num, filenames in file_groups.items():
        # Case 1: Only one face was found for this image
        if len(filenames) == 1:
            filename = filenames[0]
            identifier = f"image_{base_num}"
            print(
                f" - Processing single face: '{filename}' -> ID: '{identifier}'")

            file_path = os.path.join(NEW_FILES_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                search_results = json.load(f)

            new_data.append({
                "identifier": identifier,
                "search_results": search_results
            })

        # Case 2: Multiple faces were found for this image
        else:
            print(f" - Processing multiple faces for image_{base_num}:")
            for filename in filenames:
                match = file_pattern.match(filename)
                face_index = match.group(2)
                identifier = f"image_{base_num}_{face_index}"
                print(f"   - File: '{filename}' -> ID: '{identifier}'")

                file_path = os.path.join(NEW_FILES_DIR, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    search_results = json.load(f)

                new_data.append({
                    "identifier": identifier,
                    "search_results": search_results
                })

    print(
        f"\nWriting {len(new_data)} new entries to '{NEW_DATA_OUTPUT_PATH}'..."
    )
    with open(NEW_DATA_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)

    print(" Processing complete!")


def screen_part(json_file_path=None):


 if json_file_path is None:
    json_file_path = input("Enter path to JSON file: ")
 if not os.path.exists(json_file_path):
    print(f"Error: file '{json_file_path}' not found.")
    exit(1)
 try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise ValueError("Top-level JSON must be a list.")
 except Exception as e:
    print(f"Failed loading JSON: {e}")
    exit(1)

 print(f"Loaded {len(items)} items.")

 if not os.path.exists(BASE_OUTPUT_DIR_FOR_ALL_SEARCHES):
    os.makedirs(BASE_OUTPUT_DIR_FOR_ALL_SEARCHES)

 total_success = total_fail = 0

 for idx, item in enumerate(items, start=1):
    identifier = item.get("identifier")
    raw = item.get("search_results", [])

    # Normalize hits
    if isinstance(raw, dict):
        hits = raw.get("image_results", []) or []
    elif isinstance(raw, list):
        hits = raw
    else:
        hits = []

    if not identifier:
        print(f"[{idx}] No identifier, skipping.")
        total_fail += 1
        continue

    print(f"\n[{idx}/{len(items)}] Processing '{identifier}'")

    if not hits:
        print("  No hits found, skipping.")
        total_fail += 1
        continue

    ident_dir = os.path.join(BASE_OUTPUT_DIR_FOR_ALL_SEARCHES, identifier)
    os.makedirs(ident_dir, exist_ok=True)

    succ = fail = 0
    for i, hit in enumerate(hits, start=1):
        url = hit.get("link")
        if not url:
            print(f"  Hit {i} missing link, skipping.")
            fail += 1
            continue
        print(f"  Hit {i}/{len(hits)}: {url}")
        out_dir = os.path.join(ident_dir, f"link_{i:02d}")
        os.makedirs(out_dir, exist_ok=True)
        ok = screenshot_page_into_folder(url, out_dir)
        if ok:
            print("   ✓")
            succ += 1
        else:
            print("   ✗")
            fail += 1
            shutil.rmtree(out_dir, ignore_errors=True)

    print(f"Summary for '{identifier}': {succ} succeeded, {fail} failed")
    total_success += succ
    total_fail += fail

    if succ == 0 and os.path.isdir(ident_dir) and not os.listdir(ident_dir):
        shutil.rmtree(ident_dir)

 print(f"\nAll done: {total_success} successes, {total_fail} failures.")

def screenshot_page_into_folder(
        url,
        page_specific_output_dir,
        tile_width=VIEWPORT_WIDTH,
        tile_height=VIEWPORT_HEIGHT,
        overlap=OVERLAP_PIXELS
):
    """
    Takes tiled, overlapping screenshots of a webpage after attempting to clear pop-ups.
    """
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        if any(skip_domain in domain for skip_domain in SKIP_DOMAINS):
            print(f"Skipping URL from a blocked domain ({domain}): {url}")
            return False
    except Exception:
        pass

    driver = None
    try:
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument(f"-width={tile_width}")
        firefox_options.add_argument(f"-height={tile_height}")

        driver = webdriver.Firefox(options=firefox_options)
        driver.set_window_size(tile_width, tile_height)
        driver.set_page_load_timeout(60)

    except Exception as e_driver:
        print(f"Error initializing WebDriver for {url}: {e_driver}")
        return False

    print(f"Navigating to {url} with Selenium...")
    try:
        driver.get(url)
        print("Waiting for initial page load (5 seconds)...")
        time.sleep(5)

        handle_popups(driver)

        js_get_height = "return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );"
        total_page_height = driver.execute_script(js_get_height)
        print(f"Total page height for {url}: {total_page_height}px")

        if total_page_height == 0:
            print(f"Warning: Page height is 0 for {url}. Cannot process.")
            return False

        max_shots = 3
        if total_page_height <= tile_height:
            print("Page fits in one shot. Taking single screenshot.")
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            image_filename = f"image_{0:03d}.png"
            image_output_path = os.path.join(
                page_specific_output_dir, image_filename)
            png_data = driver.get_screenshot_as_png()
            with open(image_output_path, 'wb') as f:
                f.write(png_data)
            print(f"Saved single image: {image_output_path}")
        else:
            current_viewport_top_y = 0
            shot_index = 0
            while current_viewport_top_y < total_page_height and shot_index < max_shots:
                driver.execute_script(
                    f"window.scrollTo(0, {current_viewport_top_y});")
                time.sleep(1.5)
                image_filename = f"image_{shot_index:03d}.png"
                image_output_path = os.path.join(
                    page_specific_output_dir, image_filename)
                png_data = driver.get_screenshot_as_png()
                with open(image_output_path, 'wb') as f:
                    f.write(png_data)
                print(
                    f"Saved image {image_filename}: {image_output_path} (Viewport Y: {current_viewport_top_y})")
                shot_index += 1
                next_viewport_top_y = (
                                              current_viewport_top_y + tile_height) - overlap
                if next_viewport_top_y + tile_height >= total_page_height:
                    if current_viewport_top_y + tile_height < total_page_height and shot_index < max_shots:
                        last_tile_top_y = max(
                            0, total_page_height - tile_height)
                        if last_tile_top_y > current_viewport_top_y:
                            driver.execute_script(
                                f"window.scrollTo(0, {last_tile_top_y});")
                            time.sleep(1.5)
                            image_filename = f"image_{shot_index:03d}.png"
                            image_output_path = os.path.join(
                                page_specific_output_dir, image_filename)
                            png_data = driver.get_screenshot_as_png()
                            with open(image_output_path, 'wb') as f:
                                f.write(png_data)
                            print(
                                f"Saved final bottom image {image_filename}: {image_output_path} (Viewport Y: {last_tile_top_y})")
                    break
                if next_viewport_top_y <= current_viewport_top_y and tile_height > overlap:
                    print(
                        f"Warning for {url}: Scroll position not advancing. Stopping.")
                    break
                current_viewport_top_y = next_viewport_top_y

            if shot_index >= max_shots:
                print(
                    f"Warning for {url}: Reached maximum shot limit ({max_shots}).")

        if not os.listdir(page_specific_output_dir):
            print(f"No screenshots were generated for {url}.")
            return False
        return True

    except Exception as e_main_op:
        print(
            f"An error occurred during Selenium operation for {url}: {e_main_op}")
        return False
    finally:
        if driver:
            print(f"Closing browser for {url}...")
            driver.quit()