import googleapiclient.discovery
from dotenv import load_dotenv
from yt_dlp import YoutubeDL
import os
import yaml

dotenv_path = ".env"
load_dotenv(dotenv_path)
youtube_api_key = os.getenv("YOUTUBE_API_KEY")

# Function to read and parse the YAML file
def read_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data

def add_video_ids(video_ids):
    video_yaml_file = 'video_ids.yaml'
    video_id_content = None
    try:
        video_id_content = read_yaml(video_yaml_file)
    except Exception as e:
        video_id_content = None
    
    # Append to existing list if it exists, else create new one
    if video_id_content is None:
        video_id_content = video_ids
    else:
        video_id_content['youtube_ids'].extend(video_ids)
    
    # Save back to the YAML file
    with open(video_yaml_file, 'w') as file:
        yaml.dump(video_id_content, file, default_flow_style=False)

def get_video_ids(api_key, playlist_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    video_ids = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="contentDetails,snippet",
            playlistId=playlist_id,
            maxResults=50,  #YouTube only returns 50 at time, so need loop
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response["items"]:
            video_id = item["contentDetails"]["videoId"]
            video_ids.append((video_id))

        next_page_token = response.get("nextPageToken")

        if not next_page_token:
            break
    
    return video_ids

def get_video_ids(playlist_url):
    ydl_opts = {
        'quiet': True,  # Suppress output
        'extract_flat': True,  # Don't download videos, just retrieve metadata
        'dumpjson': True,  # Output JSON
    }

    # Process the playlist
    with YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)

    # Extract video IDs
    video_ids = [entry['id'] for entry in playlist_info['entries']]

    return video_ids

def process_playlist():
    playlist_yaml_file = 'playlist.yaml'
    playlist_content = read_yaml(playlist_yaml_file)
    playlist_ids = playlist_content.get('playlist_ids', [])
    playlist_urls = playlist_content.get('playlist_urls', [])
    
    if playlist_ids:
        for playlist_id in playlist_ids:
            video_ids = get_video_ids(youtube_api_key, playlist_id)
            add_video_ids(video_ids)

    if playlist_urls:
        for playlist_url in playlist_urls:
            video_ids = get_video_ids(playlist_url)
            add_video_ids(video_ids)
  
if __name__ == "__main__":
    process_playlist()

