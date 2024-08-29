import yaml

# Sample YAML content as a string
yaml_content = """
documents:
  AsyncWebPageReader:
    - http://asyncpage.com
    - http://fastloadingexample.com
  BrowserbaseWebReader:
    - http://browserbasedpage.com
    - http://interactivecontent.com
  FireCrawlWebReader:
    - http://firecrawlpage.com
    - http://deepcrawlingexample.com
  KnowledgeBaseWebReader:
    - http://knowledgebasepage.com
    - http://helpcontentexample.com
  MainContentExtractorReader:
    - http://maincontentpage.com
    - http://focusedcontentexample.com
  NewsArticleReader:
    - http://newsarticleexample.com
    - http://latestnewspage.com
  ReadabilityWebPageReader:
    - http://readablecontentpage.com
    - http://clearcontentexample.com
  RssNewsReader:
    - http://rssnewsexample.com/feed
    - http://newschannelrss.com/rss
  ScrapflyReader:
    - http://scrapflycontent.com
    - http://dataextractionexample.com
  SitemapReader:
    - http://sitemapexample.com/sitemap.xml
    - http://siteindexpage.com/sitemap.xml
  SpiderReader:
    - http://spidercrawlpage.com
    - http://deepcrawlingsite.com
  UnstructuredURLLoader:
    - http://unstructuredcontent.com
    - http://randomwebpageexample.com
  WholeSiteReader:
    - http://wholesiteexample.com
    - http://entiresitecontent.com
  BeautifulSoupWebReader:
    - http://beautifulsoupcontent.com
    - http://parsedhtmlpage.com
  RssReader:
    - http://rssfeedexample.com/rss
    - http://blogrssfeed.com/rss
  SimpleWebPageReader:
    - http://simplecontentpage.com
    - http://basicwebpageexample.com
  TrafilaturaWebReader:
    - http://trafilaturaexample.com
    - http://contentextractionpage.com
"""

# Load the YAML content
data = yaml.safe_load(yaml_content)

def detect_url_category(url, data):
    for category, urls in data['documents'].items():
        if url in urls:
            return category
    return None

# Traverse through all URLs and print the category for each
for category, urls in data['documents'].items():
    for url in urls:
        detected_category = detect_url_category(url, data)
        if detected_category:
            print(f"The URL '{url}' belongs to the category '{detected_category}'.")
        else:
            print(f"The URL '{url}' does not belong to any known category.")