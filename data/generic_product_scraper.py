import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin

class ProductScraper:
    def __init__(self, config):
        self.base_url = config['base_url']
        self.product_list_selector = config['product_list_selector']
        self.product_selectors = config['product_selectors']

    def fetch_page(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def parse_page(self, html):
        return BeautifulSoup(html, 'html.parser')

    def extract_product_info(self, product_element):
        product = {}
        for key, selector in self.product_selectors.items():
            element = product_element.select_one(selector)
            if key == 'link':
                product[key] = urljoin(self.base_url, element.get('href')) if element else None
            else:
                product[key] = element.text.strip() if element else None
        return product

    def scrape_product_list(self, url):
        html = self.fetch_page(url)
        if not html:
            return []

        soup = self.parse_page(html)
        product_elements = soup.select(self.product_list_selector)
        
        products = []
        for product_element in product_elements:
            product = self.extract_product_info(product_element)
            if any(product.values()):
                products.append(product)

        return products

    def scrape_product_page(self, url):
        html = self.fetch_page(url)
        if not html:
            return "Failed to fetch product page"
        
        soup = self.parse_page(html)
        
        # Try to find the description in different possible locations
        description = None
        possible_selectors = [
            'div.product__description',
            'div[data-product-description]',
            'div.product-single__description',
            'meta[name="description"]'
        ]
        
        for selector in possible_selectors:
            element = soup.select_one(selector)
            if element:
                if selector == 'meta[name="description"]':
                    description = element.get('content')
                else:
                    description = element.text.strip()
                break
        
        if not description:
            # If description is still not found, return the entire HTML structure
            return json.dumps(self.soup_to_dict(soup), indent=4)
        
        return description

    def soup_to_dict(self, soup):
        if isinstance(soup, str):
            return soup
        if isinstance(soup, bs4.element.NavigableString):
            return soup.strip()
        
        result = {}
        for child in soup.children:
            if child.name:
                result[child.name] = self.soup_to_dict(child)
        return result

def scrape_rachael_ray_cookware():
    rachael_ray_config = {
        'base_url': 'https://rachaelray.com',
        'product_list_selector': '.product-item',
        'product_selectors': {
            'title': '.product-item__title',
            'price': '.new-price',
            'link': 'a.product-link',
            'description': '.product__description'
        }
    }

    scraper = ProductScraper(rachael_ray_config)
    product_list_url = f"{rachael_ray_config['base_url']}/collections/cookware"
    products = scraper.scrape_product_list(product_list_url)

    print(f"Found {len(products)} products")

    for product in products:
        if product['link']:
            product['description'] = scraper.scrape_product_page(product['link'])
        print(json.dumps(product, indent=2))
        time.sleep(random.uniform(1, 3))  # Add a delay between requests

    # Save the results to a JSON file
    with open('rachael_ray_cookware.json', 'w') as f:
        json.dump(products, f, indent=2)

if __name__ == "__main__":
    scrape_rachael_ray_cookware()


