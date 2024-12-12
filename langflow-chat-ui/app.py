from flask import Flask, render_template, request, jsonify, send_from_directory
from langflow_api.client import LangflowClient
import os
from dotenv import load_dotenv
from flask_cors import CORS
import json

# Load environment variables
load_dotenv()
BASE_API_URL = os.getenv("BASE_API_URL", "https://api.langflow.astra.datastax.com")
LANGFLOW_ID = os.getenv("LANGFLOW_ID", "0e626e6a")
FLOW_ID = os.getenv("FLOW_ID", "123955b0")
APPLICATION_TOKEN = os.getenv("APPLICATION_TOKEN", "<YOUR_APPLICATION_TOKEN>")
ENDPOINT = os.getenv("ENDPOINT", "")

# Initialize Flask app
app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)

langflow_client = LangflowClient(BASE_API_URL, LANGFLOW_ID, FLOW_ID, APPLICATION_TOKEN)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/query', methods=['POST'])
def query():
    try:
        user_input = request.json.get('query', '')
        print(f"Received query: {user_input}")
        response = langflow_client.query(user_input + " and provide output in JSON Format")
        print(f"Langflow response: {response}")

        for key, value in response.items():
            if key == 'outputs':
                json_data = value[0]['outputs'][0]

                # Process the JSON data to remove duplicates
                if isinstance(json_data, dict):
                    for category in ['products', 'recipes']:
                        if category in json_data and isinstance(json_data[category], list):
                            unique_items = []
                            seen = set()
                            for item in json_data[category]:
                                item_tuple = tuple(item.items())
                                if item_tuple not in seen:
                                    unique_items.append(item)
                                    seen.add(item_tuple)
                            json_data[category] = unique_items

                formatted_response = {
                    "results": {
                        "text": {
                            "data": {
                                "text": f"```json\n{json.dumps(json_data, indent=2)}\n```"
                            }
                        }
                    }
                }

                print(f"Formatted response: {formatted_response}")
                return jsonify(formatted_response)

        raise ValueError("Unexpected response format from Langflow API")

    except Exception as e:
        print(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)