import yaml

# Load the YAML content from an external file
with open('urls.yml', 'r') as file:
    data = yaml.safe_load(file)

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