import yaml
from dotenv import load_dotenv
import os
import sys

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

from llama_index.readers.web import (
    AsyncWebPageReader,
    BeautifulSoupWebReader,
    BrowserbaseWebReader,
    FireCrawlWebReader,
    KnowledgeBaseWebReader,
    MainContentExtractorReader,
    NewsArticleReader,
    ReadabilityWebPageReader,
    RssNewsReader,
    RssReader,
    ScrapflyReader,
    SimpleWebPageReader,
    SitemapReader,
    SpiderWebReader,
    TrafilaturaWebReader,
    UnstructuredURLLoader,
    WholeSiteReader
)
import nltk

nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')

load_dotenv()
url_output_directory = "output"
browserbase_api_key = os.getenv("BROWSERBASE_API_KEY")
firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
scrapfly_api_key = os.getenv("SCRAPFLY_API_KEY")

# Astra DB credentials
client_id = os.getenv("ASTRA_DB_CLIENT_ID")
client_secret = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
keyspace = os.getenv("ASTRA_DB_KEY_SPACE")
secure_connect_bundle = os.getenv("ASTRA_DB_SECURE_CONNECT_BUNDLE")
config_table_name = os.getenv("ASTRA_DB_CONFIG_TABLE_NAME")
if not keyspace:
    keyspace = "default_keyspace"

# Astra DB connection
cloud_config = {
    'secure_connect_bundle': secure_connect_bundle
}
auth_provider = PlainTextAuthProvider(client_id, client_secret)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect(keyspace)

# Create folder if not exists
def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' created.")

create_folder_if_not_exists(url_output_directory)

# Base class for all readers
class BaseReader:
    def load(self, url):
        raise NotImplementedError("Each reader must implement the `load` method.")

# Individual reader classes
class AsyncWebPageReaderHandler(BaseReader):
    def load(self, url):
        return AsyncWebPageReader().load_data(urls=[url])

class BeautifulSoupWebReaderHandler(BaseReader):
    def load(self, url):
        return BeautifulSoupWebReader().load_data(urls=[url])

class BrowserbaseWebReaderHandler(BaseReader):
    def __init__(self):
        self.api_key = os.getenv("BROWSERBASE_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required for BrowserbaseWebReader")

    def load(self, url):
        return BrowserbaseWebReader(api_key=self.api_key).load_data(urls=[url])

class FireCrawlWebReaderHandler(BaseReader):
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required for FireCrawlWebReader")

    def load(self, url):
        return FireCrawlWebReader(api_key=self.api_key).load_data(urls=[url])

class KnowledgeBaseWebReaderHandler(BaseReader):
    def load(self, url):
        return KnowledgeBaseWebReader(root_url=url,link_selectors=[".mw-parser-output"], article_path="content").load_data()

class MainContentExtractorReaderHandler(BaseReader):
    def load(self, url):
        return MainContentExtractorReader().load_data(urls=[url])

class NewsArticleReaderHandler(BaseReader):
    def load(self, url):
        return NewsArticleReader(use_nlp=False).load_data(urls=[url])

class ReadabilityWebPageReaderHandler(BaseReader):
    def load(self, url):
        return ReadabilityWebPageReader().load_data(url = url)

class RSSNewsReaderHandler(BaseReader):
    def load(self, url):
        rssNewsReader = download_loader("RSSNewsReader")
        return rssNewsReader().load_data(urls=[url])

class RSSReaderHandler(BaseReader):
    def load(self, url):
        return RssReader().load_data(urls=[url])

class ScrapflyReaderHandler(BaseReader):
    def __init__(self):
        self.api_key = os.getenv("SCRAPFLY_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required for ScrapflyWebReader")

    def load(self, url):
        scrapfly_reader = ScrapflyReader(api_key=self.api_key, ignore_scrape_failures=True)
        scrapfly_scrape_config = {
            "asp": True,  # Bypass scraping blocking and antibot solutions, like Cloudflare
            "render_js": True,  # Enable JavaScript rendering with a cloud headless browser
            "proxy_pool": "public_residential_pool",  # Select a proxy pool (datacenter or residnetial)
            "country": "us",  # Select a proxy location
            "auto_scroll": True,  # Auto scroll the page
            "js": "",  # Execute custom JavaScript code by the headless browser
            }
        return scrapfly_reader.load_data(urls=[url], scrape_config=scrapfly_scrape_config, scrape_format="markdown")

class SimpleWebPageReaderHandler(BaseReader):
    def load(self, url):
        return SimpleWebPageReader().load_data(urls=[url])

class SitemapReaderHandler(BaseReader):
    def load(self, url):
        return SitemapReader().load_data(sitemap_url=url)

class SpiderWebReaderHandler(BaseReader):
    def __init__(self):
        self.api_key = os.getenv("SPIDERWEB_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required for ScrapflyWebReader")

    def load(self, url):
        return SpiderWebReader().load_data(url=url)

class TrafilaturaWebReaderHandler(BaseReader):
    def load(self, url):
        return TrafilaturaWebReader().load_data(urls=[url])

class UnstructuredURLLoaderHandler(BaseReader):
    def load(self, url):
        return UnstructuredURLLoader(urls=[url], continue_on_failure=False, headers={"User-Agent": "value"}).load_data()

class WholeSiteReaderHandler(BaseReader):
    def load(self, url):
        try:
            import chromedriver_autoinstaller
        except ImportError:
            raise ImportError("Please install chromedriver_autoinstaller")
        from llama_index.readers.web import WholeSiteReader
        from selenium import webdriver

        options = webdriver.ChromeOptions()
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument("--start-maximized")
        options.add_argument("--headless")
        chromedriver_autoinstaller.install()
        driver = webdriver.Chrome(options=options)

        # Initialize the scraper with a prefix URL and maximum depth
        scraper = WholeSiteReader(
            prefix="https://www.paulgraham.com/",
            max_depth=10,  # Example prefix
            driver=driver,  # Your custom driver with correct options
        )

        return scraper.load_data(base_url=url)

# Factory function to create readers
def reader_factory(category):
    reader_classes = {
        "AsyncWebPageReader": AsyncWebPageReaderHandler,
        "BeautifulSoupWebReader": BeautifulSoupWebReaderHandler,
        "BrowserbaseWebReader": BrowserbaseWebReaderHandler,
        "FireCrawlWebReader": FireCrawlWebReaderHandler,
        "KnowledgeBaseWebReader": KnowledgeBaseWebReaderHandler,
        "MainContentExtractorReader": MainContentExtractorReaderHandler,
        "NewsArticleReader": NewsArticleReaderHandler,
        "ReadabilityWebPageReader":ReadabilityWebPageReaderHandler,
        "RssNewsReader": RSSNewsReaderHandler,
        "RssReader":RSSReaderHandler,
        "ScrapflyReader": ScrapflyReaderHandler,
        "SimpleWebPageReader": SimpleWebPageReaderHandler,
        "SitemapReader": SitemapReaderHandler,
        "SpiderWebReader": SpiderWebReaderHandler,
        "TrafilaturaWebReader": TrafilaturaWebReaderHandler,
        "UnstructuredURLLoader": UnstructuredURLLoaderHandler,
        "WholeSiteReader": WholeSiteReaderHandler
    }
    reader_class = reader_classes.get(category)
    if not reader_class:
        raise ValueError(f"No reader found for category {category}")
    return reader_class()

# Function to sanitize file names
def sanitize_filename(url):
    file_name = url.replace("http://www.","").replace("https://www.","").replace("http://","").replace("https://","").replace("/","-")
    question_mark_position = file_name.find("?")
    file_name = file_name[:question_mark_position] if question_mark_position != -1 else file_name
    if file_name.endswith("-"):
        file_name = file_name[:-1]
    return file_name

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

query = "SELECT url, category FROM " + config_table_name + ";"
rows = session.execute(query)

# Main loop to process URLs
for url , category in rows:
    if not reader_name or category in (reader_name):
        try:
            reader = reader_factory(category)
            document = reader.load(url)
            if document:
                file_name = sanitize_filename(url)
                with open(os.path.join(url_output_directory, category+"_"+file_name), "w", encoding='utf-8') as f:
                    f.write(document[0].text)
        except Exception as e:
            with open("url_error.txt", "a", encoding='utf-8') as f:
                f.write(f"Category: {category} url: {url} {str(e)}\n")

