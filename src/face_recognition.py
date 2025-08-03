import os
import shutil
import cv2
import json
from tqdm import tqdm

from config import (
    client, MODEL_PATH, input_dir, output_dir, results_dir,
    BASE_OUTPUT_DIR_FOR_ALL_SEARCHES, base_image_dir
)
from src.enhancement import detect_foreground_faces_dl_bg_removal
from src.pipelines.person_search import read_webpage_from_image
from src.search import perform_reverse_image_search
from src.super_resolution import enhance_face_with_gfpgan_v14


def process_indices(indices_to_run):
    """
    Processes a list of images: detects and enhances faces, performs a reverse
    image search, and saves the results.
    """
    for i in indices_to_run:
        print(f"Processing image index {i}...")

        jpeg_path = os.path.join(input_dir, f"{i}.jpeg")
        jpg_path = os.path.join(input_dir, f"{i}.jpg")
        image_path = None
        if os.path.exists(jpeg_path):
            image_path = jpeg_path
        elif os.path.exists(jpg_path):
            image_path = jpg_path
        
        if not image_path:
            print(f"Warning: Image for index {i} not found. Skipping.")
            continue

        # Detect faces
        faces = detect_foreground_faces_dl_bg_removal(image_path)
        print(f"Found {len(faces)} face(s) in image {i}.")

        for j, face in enumerate(faces):
            temp_face_path = os.path.join(output_dir, f"temp_face_{i}_{j}.png")
            cv2.imwrite(temp_face_path, face)

            # Enhance the face
            enhanced_face_path = os.path.join(output_dir, f"enhanced_face_{i}_{j}.png")
            enhance_face_with_gfpgan_v14(
                img_path=temp_face_path,
                output_path=enhanced_face_path,
                upscaling_factor=2
            )

            # Perform reverse image search
            search_results_str = perform_reverse_image_search(enhanced_face_path)
            try:
                search_data = json.loads(search_results_str)
            except json.JSONDecodeError:
                print(f"Warning: Reverse image search returned invalid JSON for face {i}_{j}. Skipping.")
                continue

            image_results = search_data.get("image_results", [])

            if not image_results:
                print(f"No image_results found for face {i}_{j}. Skipping.")
                continue

            # Save the successful API response
            os.makedirs(results_dir, exist_ok=True)
            results_file_path = os.path.join(results_dir, f"results_{i}_{j}.json")
            with open(results_file_path, 'w', encoding='utf-8') as f:
                json.dump(search_data, f, indent=4, ensure_ascii=False)

            print(f"Saved {len(image_results)} image results to {results_file_path}")


def read_data():
    """
    Reads image data from a structured directory, presumably for AI processing.
    """
    if not os.path.exists(base_image_dir):
        print(f"Error: The directory specified in config 'base_image_dir' does not exist: {base_image_dir}")
        return {}

    link_dirs = [d for d in os.listdir(base_image_dir) if os.path.isdir(os.path.join(base_image_dir, d))]
    link_dirs.sort()
    all_link_data = {}

    for link_dir in tqdm(link_dirs, desc="Processing links"):
        if not link_dir.startswith("link_"):
            continue

        link_path = os.path.join(base_image_dir, link_dir)
        image_files = sorted([f for f in os.listdir(link_path) if f.endswith('.png')])

        link_data = []
        for image_file in tqdm(image_files, desc=f"Processing images in {link_dir}", leave=False):
            image_path = os.path.join(link_path, image_file)
            response = read_webpage_from_image(image_path)
            if response:
                link_data.append(response)
            else:
                print(f"Skipping {image_path} due to error.")
        all_link_data[link_dir] = link_data

    return all_link_data


def summarize_people_information(link_data):
    """
    Summarizes extracted information for people using a language model.
    """
    if not link_data:
        return None

    combined_description = "\n\n\n".join(link_data)

    try:
        response = client.chat.completions.create(
            model=MODEL_PATH,
            messages=[
                {
                    "role": "system",
                    "content": "You are a summarization assistant. Given text about people from a webpage, consolidate this information into a structured JSON output. For each unique individual, create an object with 'name', 'roles_affiliations', and 'background'. Ensure the output is a JSON array of these objects. If no people are mentioned, return an empty JSON array."
                },
                {
                    "role": "user",
                    "content": f"Summarize the information about the people mentioned in the following text:\\n\\n{combined_description}"
                }
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during summarization: {e}")
        return None


def recognize_people():
 base_dir = BASE_OUTPUT_DIR_FOR_ALL_SEARCHES

 for dir in os.listdir(base_dir):
    base_image_dir = os.path.join(base_dir, dir)

    if dir == "image_1" or dir == "image_10" or dir == "image_100":
        continue

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
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error during summarization: {e}")
            return None


    summarized_link_data = {}

    # Wrap the processing with tqdm
    for link_dir, link_data in tqdm(all_link_data.items(), desc="Summarizing link data"):
        summarized_data = summarize_people_information(link_data)
        if summarized_data:
            summarized_link_data[link_dir] = summarized_data

    import json
    from openai import OpenAI
    from collections import defaultdict

    all_candidates_info = {}
    candidate_appearance_counts = defaultdict(int)

    # Iterate through the summarized link data
    for link_dir, summarized_data in summarized_link_data.items():
        try:
            people_data = json.loads(summarized_data)

            if 'people' in people_data and isinstance(people_data['people'], list):
                people = people_data['people']
            else:
                print(
                    f"Skipping {link_dir}: 'people' key not found or is not a list in JSON.")
                continue

            for person in people:
                person_name = person.get("name")

                if person_name:
                    # Increment appearance count
                    candidate_appearance_counts[person_name] += 1

                    if person_name not in all_candidates_info:
                        all_candidates_info[person_name] = {
                            "name": person_name,
                            "roles_affiliations": [],
                            "background": []
                        }

                    roles = person.get("roles_affiliations", [])
                    if isinstance(roles, list):
                        all_candidates_info[person_name]["roles_affiliations"].extend(
                            roles)
                    else:
                        print(
                            f"Warning: roles_affiliations for {person_name} in {link_dir} is not a list.")

                    background_info = person.get("background", "")
                    if isinstance(background_info, str):
                        all_candidates_info[person_name]["background"].append(
                            background_info)
                    else:
                        print(
                            f"Warning: background for {person_name} in {link_dir} is not a string.")

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for {link_dir}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while processing {link_dir}: {e}")


    # Consolidate and prepare data for AI summarization
    candidates_for_sorting = []
    for name, info in all_candidates_info.items():
        unique_roles_affiliations = list(set(info['roles_affiliations']))
        combined_background = " ".join(info['background']).strip()
        appearance_count = candidate_appearance_counts[name]

        candidates_for_sorting.append({
            "name": info['name'],
            "roles_affiliations": unique_roles_affiliations,
            "background": combined_background,
            "appearance_count": appearance_count
        })

    # Sort candidates by appearance count in descending order
    sorted_candidates = sorted(candidates_for_sorting,
                               key=lambda x: x['appearance_count'], reverse=True)

    # Select the top 5 candidates
    top_5_candidates = sorted_candidates[:5]

    print(top_5_candidates)

  

    final_summarized_output = []

    for candidate in top_5_candidates:
        # Combine the available information for the AI
        candidate_info_text = f"Name: {candidate['name']}\nRoles/Affiliations: {', '.join(candidate['roles_affiliations'])}\nBackground: {candidate['background']}"

        try:
            response = client.chat.completions.create(
                model=MODEL_PATH,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a summarization and information extraction assistant. Given information about an individual, your task is to extract their name, roles/affiliations, and background information and then provide a concise summary. Output the results in JSON format with the following keys:
  - "name": The name of the person.
  - "roles_affiliations": A list of their key roles and affiliations extracted from the provided text.
  - "background": A concise summary of their relevant background information.
  - "summary": A brief overall summary of the individual based on all provided information.
  Ensure the extracted information is accurate and avoids repetition from the input."""
                    },
                    {
                        "role": "user",
                        "content": f"Process and summarize the following information about a candidate:\n\n{candidate_info_text}"
                    }
                ],
                response_format={"type": "json_object"}  # Specify JSON output
            )

            ai_output = json.loads(response.choices[0].message.content)

            final_summarized_output.append({
                # Use AI's name if available, otherwise original
                "name": ai_output.get('name', candidate['name']),
                "structured_info": {
                    "roles_affiliations": ai_output.get('roles_affiliations', []),
                    "background": ai_output.get('background', '')
                },
                "summary": ai_output.get('summary', 'Could not generate summary.'),
                "appearance_count": candidate['appearance_count']
            })

        except json.JSONDecodeError as e:
            print(f"Error decoding AI JSON response for {candidate['name']}: {e}")
            final_summarized_output.append({
                "name": candidate['name'],
                "structured_info": {
                    "roles_affiliations": candidate['roles_affiliations'],
                    "background": candidate['background']
                },
                "summary": f"Error processing AI response: JSON decode error - {e}",
                "appearance_count": candidate['appearance_count']
            })
        except Exception as e:
            print(f"Error processing AI response for {candidate['name']}: {e}")
            final_summarized_output.append({
                "name": candidate['name'],
                "structured_info": {
                    "roles_affiliations": candidate['roles_affiliations'],
                    "background": candidate['background']
                },
                "summary": f"An unexpected error occurred: {e}",
                "appearance_count": candidate['appearance_count']
            })

    # Print the final summarized output in a readable format
    print(json.dumps(final_summarized_output, indent=4))

    json_output_dir = "FINAL_RESULTS"
    os.makedirs(json_output_dir, exist_ok=True)

    # Save the final summarized output to a JSON file
    path = json_output_dir+'/results.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(final_summarized_output, f,  ensure_ascii=False, indent=4)