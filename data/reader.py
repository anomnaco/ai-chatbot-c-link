import yaml
from dotenv import load_dotenv
import os
import sys

from llama_index.readers.web import BeautifulSoupWebReader
from llama_index.readers.web import SimpleWebPageReader
from llama_index.readers.web import AsyncWebPageReader
from llama_index.readers.web import BrowserbaseWebReader
from llama_index.readers.web import MainContentExtractorReader
from llama_index.readers.web import NewsArticleReader
from llama_index.readers.web import ReadabilityWebPageReader
from llama_index.readers.web import TrafilaturaWebReader
from llama_index.readers.web import UnstructuredURLLoader

#Failed
#from llama_index.readers.web.firecrawl_web.base import FireCrawlWebReader
#from llama_index.readers.web import KnowledgeBaseWebReader
#from llama_index.readers.web import RssReader
#from llama_index.core.readers.web.rss_news import RSSNewsReader # ModuleNotFoundError: No module named 'llama_index.core.readers.web'
# from llama_index.readers.web import SitemapReader 
# from llama_index.readers.web import WholeSiteReader # chromedriver version mismatch

#TODO Readers
# from llama_index.readers.web import ScrapflyReader #Pending due to api key waiting for approval
# from llama_index.readers.web import SpiderWebReader #Pending due to api key need to pay to get api key

load_dotenv()
browserbase_api_key = os.getenv("BROWSERBASE_API_KEY")
firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")

# Load the YAML content from an external file
with open('urls.yml', 'r') as file:
    data = yaml.safe_load(file)

def detect_url_category(url, data):
    for category, urls in data['documents'].items():
        if url in urls:
            return category
    return None

reader_name = None
try:
    reader_name = sys.argv[1]
except:
    pass
# Traverse through all URLs and print the category for each
for category, urls in data['documents'].items():
    document = None
    for url in urls:
        detected_category = detect_url_category(url, data)
        if detected_category:
            print(f"The URL '{url}' belongs to the category '{detected_category}'.")
            if not reader_name or detected_category in (reader_name):
                if detected_category == "BeautifulSoupWebReader":
                    loader = BeautifulSoupWebReader()
                elif detected_category == "SimpleWebPageReader":
                    loader = SimpleWebPageReader()
                elif detected_category == "AsyncWebPageReader":
                    loader = AsyncWebPageReader()
                elif detected_category == "BrowserbaseWebReader":
                    loader = BrowserbaseWebReader(browserbase_api_key)
                # elif detected_category == "FireCrawlWebReader":
                #    loader = FireCrawlWebReader(api_key=firecrawl_api_key, mode="crawl")
                #    document = loader.load_data(url=url) # firecrawl_web\base.py  line 93 text=doc.get("markdown", "") fails with AttributeError: 'str' object has no attribute 'get'
                #elif detected_category == "KnowledgeBaseWebReader":
                #     loader = KnowledgeBaseWebReader(root_url=url, link_selectors=[".mw-parser-output"], article_path="content")
                #     document = loader.load_data() # knowledge_base\base.py", line 160 fails with TypeError: can only concatenate str (not "NoneType") to str
                elif detected_category == "MainContentExtractorReader":
                    loader = MainContentExtractorReader()
                elif detected_category == "NewsArticleReader":
                    loader = NewsArticleReader(use_nlp=False)
                elif detected_category == "ReadabilityWebPageReader":
                    loader = ReadabilityWebPageReader()
                    document = loader.load_data(url=url)
                elif detected_category == "RssReader":
                    loader = RssReader()
                    rss_feed_url = url
                    document = loader.load_data(urls=[rss_feed_url])
                #elif detected_category == "RSSNewsReader":
                #    RSSNewsReader = download_loader("RSSNewsReader")
                #    loader = RSSNewsReader()
                #elif detected_category == "ScrapflyReader":
                #   # Initiate ScrapflyReader with your ScrapFly API key
                #     scrapfly_reader = ScrapflyReader(
                #         api_key="Your ScrapFly API key",  # Get your API key from https://www.scrapfly.io/
                #         ignore_scrape_failures=True,  # Ignore unprocessable web pages and log their exceptions
                #     )
                #     scrapfly_scrape_config = {
                #         "asp": True,  # Bypass scraping blocking and antibot solutions, like Cloudflare
                #         "render_js": True,  # Enable JavaScript rendering with a cloud headless browser
                #         "proxy_pool": "public_residential_pool",  # Select a proxy pool (datacenter or residnetial)
                #         "country": "us",  # Select a proxy location
                #         "auto_scroll": True,  # Auto scroll the page
                #         "js": "",  # Execute custom JavaScript code by the headless browser
                #     }
                #     # Load documents from URLs as markdown
                #     document = scrapfly_reader.load_data(
                #         urls=[url],
                #         scrape_config=scrapfly_scrape_config,  # Pass the scrape config
                #         scrape_format="markdown",  # The scrape result format, either `markdown`(default) or `text`
                #     )
                #elif detected_category == "SitemapReader":
                #     loader = SitemapReader()
                #     document = loader.load_data(sitemap_url=url)
                #elif detected_category == "SpiderWebReader":
                #     loader = SpiderWebReader(api_key="YOUR_API_KEY",  mode="scrape")
                #     document = loader.load_data(url=url)
                elif detected_category == "TrafilaturaWebReader":
                    loader = TrafilaturaWebReader()
                elif detected_category == "UnstructuredURLLoader":
                    loader = UnstructuredURLLoader(urls=[url], continue_on_failure=False, headers={"User-Agent": "value"})
                    document = loader.load_data()
                #elif detected_category == "WholeSiteReader":
                #     loader = WholeSiteReader(prefix="https://www.paulgraham.com/", max_depth=10)
                #     document = loader.load_data(base_url=url)

                if not document:
                    document = loader.load_data(urls=[url])
                print(document)
        else:
            print(f"The URL '{url}' does not belong to any known category.")