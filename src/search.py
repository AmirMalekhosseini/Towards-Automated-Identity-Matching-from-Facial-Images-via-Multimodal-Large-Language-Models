from src.utils import upload_image_to_imgbb
from config import SERPAPI_API_KEY
from serpapi import GoogleSearch
import json

def perform_reverse_image_search(image_path):
    """Performs a reverse image search using SerpApi and returns results as a JSON string."""
    if not SERPAPI_API_KEY:
        print("ERROR: SERPAPI_API_KEY is not configured.")
        return json.dumps({"error": "No API key configured"})

    print("Uploading image for reverse search...")
    image_url = upload_image_to_imgbb(image_path)
    if not image_url:
        print("ERROR: Image upload failed.")
        return json.dumps({"error": "Image upload failed"})

    print(f"Performing reverse image search on: {image_url}")
    params = {
        "engine": "google_reverse_image", 
        "image_url": image_url,
        "api_key": SERPAPI_API_KEY
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()


        return json.dumps(results)
    except Exception as e:
        print(f"SerpApi search failed: {e}")
        return json.dumps({"error": str(e)})