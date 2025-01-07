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
        yaml.dump({'Products': urls}, f)

def parse_openai_response(raw_response):
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
        return config.get('products', [])
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

# Function to extract product links
def extract_product_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)]

    # Log links for debugging
    print(f"Extracted {len(links)} links. Sending to OpenAI for filtering...")

    prompt = f"""
    Here are some links extracted from a webpage:
    {links[:500]}  # Sending a sample of links

    Identify the ones most likely to lead to product pages and return them strictly in JSON format:
    {{
      "product_links": [
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
        parsed_response = parse_openai_response(raw_response)
        return parsed_response.get("product_links", []) if parsed_response else []
    except Exception as e:
        print(f"Error parsing OpenAI response for product links: {e}")
        return []

# Function to use OpenAI for extracting product info
def extract_product_info(html, url):
    prompt = f"""
    Analyze the following HTML content and extract the key product information in JSON format:
    {{
      "title": "Product Name",
      "price": "Product Price",
      "description": "Product Description",
      "images": ["Image URL 1", "Image URL 2"],
      "url": "{url}"
    }}

    HTML content:
    {html[:5000]}  # Sending only a snippet for brevity; adjust for larger HTML
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw_response = response['choices'][0]['message']['content']
        print(f"OpenAI Raw Response: {raw_response}")  # Debugging
        parsed_response = parse_openai_response(raw_response)

        # Sanitize image URLs
        if parsed_response and "images" in parsed_response:
            parsed_response["images"] = [
                clean_image_url(img_url) for img_url in parsed_response["images"]
            ]
        return parsed_response
    except Exception as e:
        print(f"Error parsing OpenAI response: {e}")
        return None


# Function to save data to file
def save_to_file(data):
    title = clean_filename(data.get('title'))
    filename = f"{title}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    filepath = os.path.join("ecommerce_sites", filename)
    os.makedirs("ecommerce_sites", exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved: {filepath}")


# Main function
def main():
    """
    Main function to process product URLs with hierarchical failure handling.
    """
    config_file = "config.yml"
    failed_urls_file = "product_failed_urls.yml"
    processed_urls_file = "product_processed_urls.yml"
    max_retries = 2  # Limit retries to avoid infinite loops
    retries = 0

    # Start with URLs from the main config file
    urls = read_urls_from_config(file=config_file)

    while urls and retries < max_retries:
        print(f"Processing cycle {retries + 1} with {len(urls)} URLs.")
        failed_sub_urls = []  # Store failed sub-URLs for this iteration
        for url in urls:
            print(f"Processing: {url}")
            try:
                html = fetch_html(url)
                if "/products/" in url:
                    print(f"Single product page detected: {url}")
                    product_links = [url]
                    product_data = extract_product_info(html, url)
                    if product_data:
                        save_to_file(product_data)
                    else:
                        failed_sub_urls.append(url)  # Sub-URL failed
                else:
                    product_links = extract_product_links(html, url)

                    if product_links:
                        print(f"Found {len(product_links)} product links.")
                        for product_url in product_links:
                            try:
                                product_html = fetch_html(product_url)
                                product_data = extract_product_info(product_html, product_url)
                                if product_data:
                                    save_to_file(product_data)
                                else:
                                    failed_sub_urls.append(product_url)  # Sub-URL failed
                            except Exception as e:
                                print(f"Error processing sub-URL {product_url}: {e}")
                                failed_sub_urls.append(product_url)
                    else:
                        print(f"No product links found for {url}. Adding to failed URLs.")
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
        processed_sub_urls.update(set(product_links) - set(failed_sub_urls))
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
