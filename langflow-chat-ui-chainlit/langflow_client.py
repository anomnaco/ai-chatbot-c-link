import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LangflowClient:
    def __init__(self, base_api_url, langflow_id, flow_id, application_token):
        self.base_api_url = base_api_url
        self.langflow_id = langflow_id
        self.flow_id = flow_id
        self.api_url = f"{base_api_url}/lf/{langflow_id}/api/v1/run/{flow_id}?stream=false"
        token = application_token.strip()
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        logger.info(f"Initialized LangflowClient with API URL: {self.api_url}")

    def query(self, input_value):
        payload = {
            "input_value": input_value,
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": {
                "ChatInput-mE8Jx": {},
                "Agent-GjLDC": {},
                "AstraDBToolComponent-6soEY": {},
                "AstraDBToolComponent-TAX3n": {},
                "AstraDBToolComponent-oekSk": {},
                "TextOutput-a8on9": {}
            }
        }

        try:
            logger.info(f"Sending request to Langflow API with input: {input_value}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=500  # Add timeout
            )

            # Log response status and headers
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")

            if response.status_code == 401:
                raise Exception("Authentication failed. Please check your application token.")
            elif response.status_code == 404:
                raise Exception("API endpoint not found. Please check your Langflow ID and Flow ID.")

            response.raise_for_status()

            # Try to parse JSON response
            try:
                return response.json()
            except ValueError:
                logger.error(f"Invalid JSON response: {response.text}")
                raise Exception("Invalid response format from server")

        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to {self.api_url}")
            raise Exception("Could not connect to the server. Please check your internet connection and API URL.")
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            raise Exception("Request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise Exception(f"Request failed: {str(e)}")