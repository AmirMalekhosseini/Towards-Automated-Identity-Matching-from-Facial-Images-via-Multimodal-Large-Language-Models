import base64
import json
import os
import shutil

import cv2
from tqdm import tqdm

from config import output_dir, results_dir, input_dir, client, MODEL_PATH, base_image_dir
from src.enhancement import detect_foreground_faces_dl_bg_removal
from src.search import perform_reverse_image_search
from src.super_resolution import enhance_face_with_gfpgan_v14


def find_results():
 os.makedirs(results_dir, exist_ok=True)
 os.makedirs(output_dir, exist_ok=True)


 indecies_to_run = [3, 15, 21]

# Iterate through the images in the input directory
 for i in indecies_to_run:
    print("Processing " + str(i) + "...")
    image_path_jpeg = os.path.join(input_dir, f"{i}.jpeg")
    image_path_jpg = os.path.join(input_dir, f"{i}.jpg")

    if os.path.exists(image_path_jpeg):
        image_path = image_path_jpeg
    elif os.path.exists(image_path_jpg):
        image_path = image_path_jpg
    else:
        continue

    # Detect faces in the image
    faces = detect_foreground_faces_dl_bg_removal(image_path)

    # Enhance the faces
    for j, face in enumerate(faces):
        # Save the face to a temporary file
        temp_face_path = os.path.join(output_dir, f"temp_face_{j}.png")
        cv2.imwrite(temp_face_path, face)

        # Enhance the face
        enhanced_face_path = os.path.join(output_dir, f"enhanced_face_{j}.png")
        restored_tensor = enhance_face_with_gfpgan_v14(
            img_path=temp_face_path,
            output_path=enhanced_face_path,
            upscaling_factor=2
        )

        # Perform reverse image search
        search_results = perform_reverse_image_search(enhanced_face_path)
        items = (json.loads(search_results))
        search_results = items["organic"]

        # Save the search results
        if search_results:
            results_file_path = os.path.join(results_dir, f"results_{i}_{j}.json")
            with open(results_file_path, 'w') as f:
                json.dump(search_results, f, indent=4)

    # Remove the temporary directories
    shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    shutil.make_archive("dip_results_new", 'zip', "/content/reverse_image_search_results_new")



 import base64
from openai import OpenAI
from PIL import Image
import io
import socket
socket.setdefaulttimeout(120)  
import httpx
from httpx import Timeout
from together import Together
import requests

# Configure requests with retry
transport = httpx.HTTPTransport(retries=5)
timeout = Timeout(60.0)  # 60 seconds timeout
http_client = httpx.Client(transport=transport, timeout=timeout)

def read_webpage_from_image(image_path):
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        exit()

    with io.BytesIO() as buffer:
        img.save(buffer, format=img.format)
        img_bytes = buffer.getvalue()

    base64_image = base64.b64encode(img_bytes).decode('utf-8')

    data_url = f"data:image/{img.format.lower()};base64,{base64_image}"


    def get_available_models():
        """Get list of available models from Together API"""
        url = "https://api.together.xyz/v1/models"
        headers = {"Authorization": f"Bearer {'e218d1e81ec7d027b5d5ec76fe40610a3f8df03cbc061f9a54d7800cb449eadc'}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            models = response.json()  # Directly get the list of models
            # Filter for vision models
            vision_models = [model["display_name"] for model in models
                             if "vision" in model["display_name"].lower()]
            return vision_models
        print(f"Error fetching models: {response.status_code}")
        return []
    vision_models = get_available_models()
    model_name = vision_models[0]
    print(f"Using vision model: {model_name}")

    system_1 = """You are a web page content extractor. Given a screenshot of a web page, your task is to extract all visible textual information in a clean, structured format. Focus on preserving layout, section hierarchy, and the correct spelling of names, places, organizations, and other key entities in both English and their original languages (if shown).

If a query is provided (e.g., "Who are the people mentioned on this page?" or "What is their professional background?"), prioritize extracting information relevant to the query, such as:

* Names of people featured
* Their roles, occupations, affiliations, or activities
* Descriptions or bios
* Any associated images with captions

Ensure that:

* Noise (ads, boilerplate UI elements) is excluded
* The output is suitable for downstream use in large language models
* Any multilingual text is preserved as shown

Present the output as structured JSON or a clearly sectioned plain text format, depending on the use case."""

    system_2 = """You are a web page content extractor. Given a screenshot of a web page, your task is to extract the most prominent individuals mentioned or shown on the page, along with relevant details about them.

Focus on:

* Full names (in English and original language, if present)
* Roles, professions, or affiliations
* Brief descriptions or biographies
* Associated images or captions if available and relevant

**Only extract individuals who appear central or significant to the content of the page**—e.g., those featured in headlines, main sections, or accompanied by detailed descriptions. Do not include people mentioned in passing or in unrelated UI elements, comments, or ads.

If a specific query is provided (e.g., “Who are the key people on this page?”), prioritize extracting information that answers that query clearly.

Ensure the output is:

* Clean and structured
* Free from irrelevant UI text or clutter
* Suitable for downstream processing by language models

Format the output as structured JSON or clearly sectioned plain text, based on the intended use.

"""


    response = client.chat.completions.create(
        model=MODEL_PATH,
        messages=[
            {
                "role": "system",
                "content": system_2,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url}
                    },
                    {"type": "text", "text": "What are the central people present in the given screenshot of the web page, list them and their background and information."}
                ]
            }
        ],
    )

    return response.choices[0].message.content

def extract_people():
 all_link_data = {}

# Get list of link directories
 link_dirs = [d for d in os.listdir(base_image_dir) if os.path.isdir(
 os.path.join(base_image_dir, d))]
 link_dirs.sort()  

# Wrap the outer loop with tqdm
 for link_dir in tqdm(link_dirs, desc="Processing links"):
    print(link_dir)
    if not link_dir.startswith("link_"):
        continue

    link_path = os.path.join(base_image_dir, link_dir)
    image_files = [f for f in os.listdir(link_path) if f.endswith('.png')]
    image_files.sort()  

    link_data = []
    # Wrap the inner loop with tqdm
    for image_file in tqdm(image_files, desc=f"Processing images in {link_dir}", leave=False):
        image_path = os.path.join(link_path, image_file)
        print(image_path)
        response = read_webpage_from_image(image_path)
        print(response)

        if response:
            link_data.append(response)
        else:
            print(f"Skipping {image_path} due to error.")

    all_link_data[link_dir] = link_data


#%%
def summarize_people_information(link_data):
    """
    Summarizes the extracted information for people from a list of descriptions
    related to a single link using a language model, outputting JSON.

    Args:
      link_data: A list of strings, where each string is a description
                 extracted from an image related to the same link.

    Returns:
      A string containing the summarized information about people in JSON format,
      or None if an error occurred or no data was processed.
    """
    if not link_data:
        return None

    # Combine all descriptions for the link into a single text
    combined_description = "\n\n\n".join(link_data)



    try:
        response = client.chat.completions.create(
            model=MODEL_PATH,
            messages=[
                {
                    "role": "system",
                    "content": """You are a summarization assistant. Given a collection of text descriptions about people found on a webpage, your task is to consolidate this information into a structured JSON output. For each unique individual mentioned, create a JSON object with the following keys:

- "name": The name of the person.
- "roles_affiliations": A list of their roles and affiliations.
- "background": A summary of their relevant background information.

Ensure the output is a JSON array of these objects. If no people are mentioned, return an empty JSON array.""",
                },
                {
                    "role": "user",
                    "content": f"Summarize the information about the people mentioned in the following text:\n\n{combined_description}"
                }
            ],
            # Add response_format to instruct the model to return JSON
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during summarization: {e}")
        return None

