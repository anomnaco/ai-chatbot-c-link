import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin, urlparse
import logging
from concurrent.futures import ThreadPoolExecutor
import re, os

class EcommerceCrawler:
    def __init__(self, config):
        self.base_url = config['base_url']
        self.selectors = config['selectors']
        self.max_pages = config.get('max_pages', float('inf'))
        self.delay = config.get('delay_range', (1, 3))
        self.visited_urls = set()
        self.products = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        # Create directory if not present
        self.folder_path = "ecommerce_sites"
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
        self.logger = logging.getLogger(__name__)

    def get_headers(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Firefox/89.0'
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def fetch_page(self, url, retries=3):
        for attempt in range(retries):
            try:
                response = requests.get(
                    url,
                    headers=self.get_headers(),
                    timeout=10
                )
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == retries - 1:
                    return None
                time.sleep(random.uniform(2, 5))
        return None

    def parse_product_links(self, soup):
        links = []
        if self.selectors.get('product_link'):
            products = soup.select(self.selectors['product_link'])
            # for product in products:
            for index, product in enumerate(products):
                href = product.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    links.append(full_url)
                # if index >= 1:
                #     break
        return links

    def parse_pagination_links(self, soup):
        links = []
        if self.selectors.get('pagination'):
            pagination = soup.select(self.selectors['pagination'])
            for link in pagination:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    links.append(full_url)
        return links

    def extract_product_info(self, soup, url):
        product = {'url': url}
        
        product_html = self.fetch_page(url)
        product_soup = BeautifulSoup(product_html, 'html.parser')
        
        # Extract basic product information
        for field, selector in self.selectors.items():
            if field not in ['product_link', 'pagination']:
                elements = product_soup.select(selector)

                if elements:
                    # Handle different types of content
                    if field == 'price':
                        # Clean up price text
                        price_text = elements[0].text.strip()
                        price = re.findall(r'\d+\.?\d*', price_text)
                        product[field] = price[0] if price else None
                    elif field == 'images':
                        # Extract all image URLs
                        product[field] = [
                            urljoin(self.base_url, img.get('src'))
                            for img in elements if img.get('src')
                        ]
                    else:
                        product[field] = (elements[0].text.strip()).split("\n")[0]
                else:
                    if field == 'description' and not elements:
                        description_tag = soup.find("meta", attrs={"name": "description"})
                        if description_tag and "content" in description_tag.attrs:
                            description = description_tag["content"]
                            product[field] = description
                    else:
                        product[field] = None
        
        return product

    def crawl_product_page(self, url):
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        html = self.fetch_page(url)
        if not html:
            return

        parsed_url = urlparse(url)
        ending_portion = parsed_url.path.split("/")[-1]

        soup = BeautifulSoup(html, 'html.parser')
        product_info = self.extract_product_info(soup, url)
        with open(self.folder_path + "/" + ending_portion +".json", "w", encoding="utf-8") as file:
                json.dump(product_info, file, indent=4)

        if any(product_info.values()):
            self.products.append(product_info)
            self.logger.info(f"Scraped product: {product_info.get('title', url)}")

        time.sleep(random.uniform(*self.delay))

    def crawl_category_page(self, url, current_page=1):
        if current_page > self.max_pages:
            return

        self.logger.info(f"Crawling category page {current_page}: {url}")
        html = self.fetch_page(url)
        if not html:
            return

        soup = BeautifulSoup(html, 'html.parser')
        product_links = self.parse_product_links(soup)
        
        # Use ThreadPoolExecutor for parallel processing of product pages
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(self.crawl_product_page, product_links)

        # Handle pagination
        pagination_links = self.parse_pagination_links(soup)
        for next_page in pagination_links:
            if next_page not in self.visited_urls:
                self.crawl_category_page(next_page, current_page + 1)

    def save_results(self, filename='products.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Saved {len(self.products)} products to {filename}")

def crawl_rachael_ray():
    config = {
        'base_url': 'https://rachaelray.com',
        'selectors': {
            'product_link': 'a.product-link',
            'pagination': '.pagination__nav a',
            'title': '.product__title__wrapper',
            'price': '.product__price__wrap',
            'description': '.product__description',
            'images': '.product-item__image img'
        },
        'max_pages': 5,  # Limit the number of pages to crawl
        'delay_range': (1, 3)  # Random delay between requests
    }

    crawler = EcommerceCrawler(config)
    crawler.crawl_category_page('https://rachaelray.com/collections/cookware')
    crawler.save_results('rachael_ray_products.json')

if __name__ == "__main__":
    crawl_rachael_ray()