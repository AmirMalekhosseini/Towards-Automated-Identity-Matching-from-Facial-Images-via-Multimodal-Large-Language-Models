from config import NEW_DATA_OUTPUT_PATH
from src.face_recognition import process_indices,recognize_people
from src.screenshot import screen_part, process_new_json_files


def run():
     indices_to_run = [26]
     process_indices(indices_to_run)

     process_new_json_files()

     screen_part(NEW_DATA_OUTPUT_PATH)

     recognize_people()

