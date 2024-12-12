import requests

class LangflowClient:
    def __init__(self, base_api_url, langflow_id, flow_id, application_token):
        self.api_url = f"{base_api_url}/lf/{langflow_id}/api/v1/run/{flow_id}?stream=false"
        token = application_token.strip()
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

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
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            response.raise_for_status()  # Raise error for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    client = LangflowClient(
        base_api_url="https://api.langflow.astra.datastax.com",
        langflow_id="0e626e6a-409f-4ad8-916e",
        flow_id="123955b0-5a90-4227-9197",
        application_token="AstraCS:ddUepx:aa"
    )
    response = client.query("Get products and recipes with chicken")
    print(response)
