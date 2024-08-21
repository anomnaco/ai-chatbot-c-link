import yaml
import os
import sys
#one_levels_up = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#sys.path.append(one_levels_up)
#from data.compile_documents import add_documents

from youtube_transcript_api import YouTubeTranscriptApi

# Function to read and parse the YAML file
def read_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

# Example usage
yaml_file = 'video_ids.yaml'  # Replace with your YAML file path
yaml_content = read_yaml(yaml_file)

def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' created.")
    else:
        print(f"Folder '{folder_path}' already exists.")

# Example usage:
create_folder_if_not_exists("video_output")

# Access and list the YouTube IDs
video_ids = yaml_content.get('youtube_ids', [])
for video_id in video_ids:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    folder = "video_output/"
    file_name = folder + "1-"+str(video_id)+ "-1.txt"
    temp = " ".join([item["text"] for item in transcript])
    with open(file_name, "w") as f:
        f.write(temp)

