
import httpx
from httpx import Timeout
from openai import OpenAI


NOISE_TYPES = ['gaussian', 'salt_pepper', 'poisson']
DENOISE_METHODS = ['median', 'gaussian', 'bilateral', 'nl_means']

# Set to True to enforce SSL, False to bypass (USE WITH CAUTION)
DOWNLOAD_VERIFY_SSL = False

# SECURELY LOADED KEYS 
CLIENT_ID = "20e4966a6fa2217"
API_KEY = "eyJhbGciOiJIUzI1NiIsImtpZCI6IlV6SXJWd1h0dnprLVRvdzlLZWstc0M1akptWXBvX1VaVkxUZlpnMDRlOFUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJnb29nbGUtb2F1dGgyfDEwNTM3MjMxMjQxNDUzNTQzMTc5MSIsInNjb3BlIjoib3BlbmlkIG9mZmxpbmVfYWNjZXNzIiwiaXNzIjoiYXBpX2tleV9pc3N1ZXIiLCJhdWQiOlsiaHR0cHM6Ly9uZWJpdXMtaW5mZXJlbmNlLmV1LmF1dGgwLmNvbS9hcGkvdjIvIl0sImV4cCI6MTkwNzE0NjM3NiwidXVpZCI6IjViNzg5NTM1LTVlNTAtNGUyOS1hNzRkLTNkZTNiNjJkYWZmMCIsIm5hbWUiOiJnZW1tYSIsImV4cGlyZXNfYXQiOiIyMDMwLTA2LTA4VDEwOjUyOjU2KzAwMDAifQ.uECdE4atip3AHB-tppM9udBS9uqnrEXcE0OIKiqFmQw"
SERPAPI_API_KEY = "32656e1dd449344a0fb50819727b900edf14423882fdb1863ad2dca10638dbb8"
IMGBB_API_KEY = "dfac5225c08c99ea4db6511c2ae1ff3e"

# PATHS
OUTPUT_DIRECTORY = "enhanced_images_output"
ORIGINAL_FACES_PATH = "faces_foreground_dl"
ENHANCED_FACES_PATH = "faces_enhanced"
BASE_OUTPUT_DIR_FOR_ALL_SEARCHES = "reverse_image_search_outputs"
input_dir = "Images"
output_dir = "Output"
results_dir = "reverse_image_search_results_new"
NEW_FILES_DIR = 'reverse_image_search_results_new/'
NEW_DATA_OUTPUT_PATH = 'newly_processed_results.json'

# ENHANCEMENT FACTORS 
SHARPNESS_FACTOR = 1.5
CONTRAST_FACTOR = 1.3
BRIGHTNESS_FACTOR = 1.2

# SCREENSHOT SETTINGS 
VIEWPORT_WIDTH = 1024
VIEWPORT_HEIGHT = 1000
OVERLAP_PIXELS = 100
SKIP_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "pinterest.com",
    "quora.com",
    "x.com",
]

#  CLIENT DEFINITION 
MODEL_PATH = "google/gemma-3-27b-it"
client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=API_KEY,
)
base_image_dir = "/content/links/image_18"

transport = httpx.HTTPTransport(retries=5)
timeout = Timeout(60.0)
http_client = httpx.Client(transport=transport, timeout=timeout)
