import requests
import re
import os
import json
import yaml
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from datetime import datetime
import openai
from dotenv import load_dotenv

# Load environment variables (including API key) from .env file
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def write_urls_to_yaml(file, urls):
    """
    Writes a list of URLs to a YAML file.

    Args:
        file (str): Path to the YAML file.
        urls (list): List of URLs to write.
    """
    with open(file, 'w') as f:
        yaml.dump({'Recipes': urls}, f)

def parse_openai_response(raw_response, url):
    # Remove backticks if the response is wrapped in a code block
    raw_response = raw_response.strip()
    if raw_response.startswith("```") and raw_response.endswith("```"):
        raw_response = raw_response[3:-3].strip()  # Remove leading and trailing backticks
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None

# Function to read URLs from config.yml
def read_urls_from_config(file="config.yml"):
    """
    Reads URLs from a YAML configuration file.

    Args:
        file (str): Path to the YAML file.

    Returns:
        list: List of URLs.
    """
    try:
        with open(file, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('recipes', [])
    except FileNotFoundError:
        print(f"File {file} not found.")
        return []

# Function to clean image url
def clean_image_url(url):
    """
    Remove query parameters from the image URL.
    Args:
        url (str): The original image URL.
    Returns:
        str: The sanitized image URL.
    """
    return url.split("?")[0] if "?" in url else url

# Function to clean filenames
def clean_filename(name):
    return re.sub(r'[^\w\s-]', '', name).replace(" ", "_")


# Function to fetch HTML content
def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

# Function to extract Recipe links
def extract_recipe_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)]

    # Log links for debugging
    print(f"Extracted {len(links)} links. Sending to OpenAI for filtering...")

    prompt = f"""
    Here are some links extracted from a webpage:
    {links[:500]}  # Sending a sample of links

    Identify the ones most likely to lead to recipe pages and return them strictly in JSON format:
    {{
      "recipe_links": [
        "link1",
        "link2",
        ...
      ]
    }}
    Do not include explanations or code.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw_response = response['choices'][0]['message']['content']
        print(f"OpenAI Raw Response: {raw_response}")  # Debugging
        parsed_response = parse_openai_response(raw_response, base_url)
        return parsed_response.get("recipe_links", []) if parsed_response else []
    except Exception as e:
        print(f"Error parsing OpenAI response for recipe links: {e}")
        return []

def extract_ing_ins_info(soup, cls_name, search):
    section = soup.find('div', class_=cls_name)
    ing_ins = []
    if section:
        ing_ins = [item.get_text(strip=True) for item in section.find_all(search)]
    return ing_ins

def extract_instructions_info(soup):
    instructions_section = soup.find('div', class_='recipe-instructions')
    instructions = []
    if instructions_section:
        instructions = [item.get_text(strip=True) for item in instructions_section.find_all('p')]
    return instructions

def extract_video_info(soup):
    """
    Extracts video information from the HTML soup.

    Args:
        soup (BeautifulSoup): Parsed HTML content.

    Returns:
        dict: Video information including title, URL, duration, keywords, author, and publish date.
    """
    video_info = {}
    video_player = soup.find('div', class_='cvp-player')
    if video_player:
        video_info = {
            'video_title': video_player.get('data-title', ''),
            'video_url': video_player.get('data-hls', ''),
            'video_duration': video_player.get('data-duration', ''),
            'video_keywords': video_player.get('data-keywords', ''),
        }
        try:
            tracking_data = json.loads(video_player.get('data-tracking-data', '{}'))
            video_info['video_author'] = tracking_data.get('authorName', '')
            video_info['video_publish_date'] = tracking_data.get('assetPubDate', '')
        except json.JSONDecodeError:
            print("Failed to parse video tracking data")
    return video_info

# Function to use OpenAI for extracting recipe info
def extract_recipe_info(html, url):
    soup = BeautifulSoup(html, "html.parser")
    # Extract video information using the separate method
    video_info = extract_video_info(soup)
    ingredients = extract_ing_ins_info(soup,'recipe-ingredients', 'li')
    instructions = extract_ing_ins_info(soup,'recipe-instructions', 'p')

    prompt = f"""
    Analyze the following HTML content and extract the key recipe information in JSON format:
    {{
      "title": "Recipe Title",
      "description": "Recipe Description",
      "category": "Recipe type",
      "ingredients": "Recipe Ingredients",
      "instructions": "Recipe Instructions",
      "image_url": ["Image URL 1", "Image URL 2"],
      "video_info": {json.dumps(video_info)},
      "url": "{url}"
    }}

    HTML content:
    {html[:2000]}  # Sending only a snippet for brevity; adjust for larger HTML
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw_response = response["choices"][0]["message"]["content"]
        print(f"OpenAI Raw Response: {raw_response}")  # Debugging
        parsed_response = parse_openai_response(raw_response, url)

        # Sanitize image URLs
        if parsed_response and "image_url" in parsed_response:
            parsed_response["image_url"] = [
                clean_image_url(img_url) for img_url in parsed_response["image_url"]
            ]
        if parsed_response:
            # Merge OpenAI response with video info
            parsed_response["video_info"] = video_info
            parsed_response["ingredients"] = [ing.strip() for ing in ingredients]
            parsed_response["instructions"] = [ing.strip() for ing in instructions]
            return parsed_response
        else:
            return {'video_info': video_info}  # Return only video info if OpenAI fails
    except Exception as e:
        print(f"Error parsing OpenAI response: {e}")
        return None


# Function to save data to file
def save_to_file(data):
    title = clean_filename(data.get('title'))
    filename = f"{title}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    filepath = os.path.join("recipes_sites", filename)
    os.makedirs("recipes_sites", exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved: {filepath}")


# Main function
def main(reprocess=False):
    """
    Main function to process recipe URLs with hierarchical failure handling.
    """
    config_file = "config.yml"
    failed_urls_file = "recipe_failed_urls.yml"
    processed_urls_file = "recipe_processed_urls.yml"
    max_retries = 2  # Limit retries to avoid infinite loops
    retries = 0

    # Start with URLs from the main config file
    urls = read_urls_from_config(file=config_file)

    while urls and retries < max_retries:
        print(f"Processing cycle {retries + 1} with {len(urls)} URLs.")
        failed_sub_urls = []  # Store failed sub-URLs for this iteration
        for url in urls:
            try:
                html = fetch_html(url)
                if "/recipes/" in url:
                    print(f"Single recipe page detected: {url}")
                    recipe_links = [url]
                    recipe_data = extract_recipe_info(html, url)
                    if recipe_data:
                        save_to_file(recipe_data)
                    else:
                        failed_sub_urls.append(url)  # Sub-URL failed
                else:
                    recipe_links = extract_recipe_links(html, url)

                    if recipe_links:
                        print(f"Found {len(recipe_links)} recipe links.")
                        for recipe_url in recipe_links:
                            try:
                                recipe_html = fetch_html(recipe_url)
                                recipe_data = extract_recipe_info(recipe_html, recipe_url)
                                if recipe_data:
                                    save_to_file(recipe_data)
                                else:
                                    failed_sub_urls.append(recipe_url)  # Sub-URL failed
                            except Exception as e:
                                print(f"Error processing sub-URL {recipe_url}: {e}")
                                failed_sub_urls.append(recipe_url)
                    else:
                        print(f"No recipe links found for {url}. Adding to failed URLs.")
                        failed_sub_urls.append(url)
            except Exception as e:
                print(f"Error processing {url}: {e}")
                failed_sub_urls.append(url)

            # Update the failed URLs file
            if failed_sub_urls:
                print(f"{len(failed_sub_urls)} sub-URLs failed processing.")
                write_urls_to_yaml(failed_urls_file, failed_sub_urls)
            else:
                print("All sub-URLs processed successfully.")
                break

        # Move successfully processed sub-URLs to processed_urls_file
        processed_sub_urls = set(read_urls_from_config(file=processed_urls_file))
        processed_sub_urls.update(set(recipe_links) - set(failed_sub_urls))
        write_urls_to_yaml(processed_urls_file, list(processed_sub_urls))

        # Prepare for the next cycle with failed sub-URLs
        urls = failed_sub_urls
        retries += 1

        if retries >= max_retries:
            print("Max retries reached. Some sub-URLs could not be processed.")
        elif not urls:
            print("All URLs processed successfully.")
if __name__ == "__main__":
    main()
