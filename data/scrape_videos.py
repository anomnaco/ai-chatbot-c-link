import yaml
import os

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


# Example usage:
create_folder_if_not_exists("video_output")

# Access and list the YouTube IDs
video_ids = yaml_content.get('youtube_ids', [])
folder = "video_output/"
for video_id in video_ids:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        file_name = folder + "1-"+str(video_id)+ "-1.txt"
        temp = " ".join([item["text"] for item in transcript])
        with open(file_name, "w") as f:
            f.write(temp)
    except Exception as e:
        with open("video_ids_error.txt", "a") as f:
            f.write(video_id + "\n")
