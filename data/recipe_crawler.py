import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin
import logging
import os
from typing import Dict, List, Any

class RecipeCrawler:
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config['base_url']
        self.max_pages = config.get('max_pages', float('inf'))
        self.delay_range = config.get('delay_range', (1, 3))
        self.visited_urls = set()
        self.recipes = []

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.folder_path = "recipes"
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
        self.logger = logging.getLogger(__name__)

    def fetch_page(self, url: str, retries: int = 3) -> str:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == retries - 1:
                    return None
                time.sleep(random.uniform(2, 5))
        return None

    def extract_recipe_info(self, soup: BeautifulSoup, article: Any) -> Dict[str, Any]:
        title = article.find(class_='field--name-field-display-headline')
        description = article.find(class_='field--name-field-subhead')
        category = article.find(class_='field--name-field-category')
        image = article.find(class_='field--name-field-image-landscape')
        link = article.find('a', class_='card-wrapper-link')

        video_player = article.find('div', class_='cvp-player')
        video_info = {}
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
                self.logger.error("Failed to parse video tracking data")

        return {
            'title': title.text.strip() if title else 'No title found',
            'description': description.text.strip() if description else 'No description found',
            'link': urljoin(self.base_url, link['href']) if link and 'href' in link.attrs else 'No link found',
            'image_url': image.find('img')['src'] if image and image.find('img') else 'No image found',
            'category': category.text.strip() if category else 'No category found',
            'date_scraped': time.strftime("%Y-%m-%d %H:%M:%S"),
            'video_info': video_info
        }

    def crawl_recipe_page(self, url: str):
        if url in self.visited_urls:
            return

        self.visited_urls.add(url)
        self.logger.info(f'Crawling recipe: {url}')
        html = self.fetch_page(url)
        if not html:
            return

        soup = BeautifulSoup(html, 'html.parser')
        recipe = {
            'url': url,
            'title': soup.find('h1').text.strip() if soup.find('h1') else '',
            'description': soup.find(class_='field--name-field-subhead').text.strip() if soup.find(class_='field--name-field-subhead') else '',
            'category': soup.find(class_='field--name-field-category').text.strip() if soup.find(class_='field--name-field-category') else '',
            'image_url': '',
            'video_info': {}
        }

        image_meta = soup.find('meta', property='og:image')
        if image_meta and 'content' in image_meta.attrs:
            clean_url = image_meta['content'].split('?')[0]
            recipe['image_url'] = clean_url

        video_player = soup.find('div', class_='cvp-player')
        if video_player:
            recipe['video_info'] = {
                'video_title': video_player.get('data-title', ''),
                'video_url': video_player.get('data-hls', ''),
                'video_duration': video_player.get('data-duration', ''),
                'video_keywords': video_player.get('data-keywords', ''),
            }
            try:
                tracking_data = json.loads(video_player.get('data-tracking-data', '{}'))
                recipe['video_info']['video_author'] = tracking_data.get('authorName', '')
                recipe['video_info']['video_publish_date'] = tracking_data.get('assetPubDate', '')
            except json.JSONDecodeError:
                self.logger.error("Failed to parse video tracking data")

        ingredients_section = soup.find('div', class_='recipe-ingredients')
        if ingredients_section:
            ingredients = [item.get_text(strip=True) for item in ingredients_section.find_all('li')]
            recipe['ingredients'] = [ing.strip() for ing in ingredients]

        instructions_section = soup.find('div', class_='recipe-instructions')
        if instructions_section:
            instructions = [item.get_text(strip=True) for item in instructions_section.find_all('p')]
            recipe['instructions'] = [inst.strip() for inst in instructions]

        filename = f"{recipe['title'].lower().replace(' ', '-')[:50]}.json"
        filename = filename.replace('|', ' ').replace('"', ' ').replace('&', ' and ')
        with open(os.path.join(self.folder_path, filename), 'w', encoding='utf-8') as file:
            json.dump(recipe, file, indent=4, ensure_ascii=False)

        self.recipes.append(recipe)
        time.sleep(random.uniform(*self.delay_range))

    def crawl_listing_page(self, url: str, current_page: int = 1):
        if current_page > self.max_pages:
            return

        self.logger.info(f"Crawling listing page {current_page}: {url}")
        html = self.fetch_page(url)
        if not html:
            return

        soup = BeautifulSoup(html, 'html.parser')
        recipe_articles = soup.find_all('article', class_=['recipe', 'teaser-large', 'card-large'])

        for index, article in enumerate(recipe_articles):
            self.logger.info(f"Processing recipe {index + 1} on page {current_page}")
            recipe_info = self.extract_recipe_info(soup, article)
            self.logger.info(f"Extracted recipe info: {recipe_info}")
            if recipe_info['title'] == 'No title found':
                continue
            self.crawl_recipe_page(recipe_info['link'])

        next_page = soup.find('li', class_='next')
        if next_page and next_page.find('a'):
            next_url = urljoin(self.base_url, next_page.find('a')['href'])
            if next_url not in self.visited_urls:
                self.crawl_listing_page(next_url, current_page + 1)

    def save_results(self, filename: str = 'all_recipes.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.recipes, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Saved {len(self.recipes)} recipes to {filename}")

def main():
    config = {
        'base_url': 'https://www.rachaelrayshow.com',
        'max_pages': 5,
        'delay_range': (1, 3)
    }

    crawler = RecipeCrawler(config)
    crawler.crawl_listing_page('https://www.rachaelrayshow.com/recent/recipe')
    crawler.save_results()

if __name__ == "__main__":
    main()