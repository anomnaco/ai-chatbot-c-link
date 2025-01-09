import chainlit as cl
from langflow_client import LangflowClient
import os
from dotenv import load_dotenv
import json
import logging
import re
import time

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Langflow Client
BASE_API_URL = os.getenv("BASE_API_URL")
LANGFLOW_ID = os.getenv("LANGFLOW_ID")
FLOW_ID = os.getenv("FLOW_ID")
APPLICATION_TOKEN = os.getenv("APPLICATION_TOKEN")

try:
    langflow_client = LangflowClient(BASE_API_URL, LANGFLOW_ID, FLOW_ID, APPLICATION_TOKEN)
    print("LangflowClient initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LangflowClient: {str(e)}")
    raise


@cl.on_chat_start
async def start():
    await cl.Message("Welcome to Recipe and Product Search! Enter your search query to get started.").send()


@cl.on_message
async def main(message: cl.Message):
    try:
        temp_msg = cl.Message(content="Searching...")
        await temp_msg.send()

        # response = langflow_client.query(message.content + ". Group them based on results. Provide output in JSON Format")

        response = langflow_client.query(message.content + ". Group them. Provide output in JSON Format.")
        logger.info(f"Stage 1 received response")

        if not response or 'outputs' not in response or not response['outputs']:
            await cl.Message("No results found. Please try again.").send()
            logger.info("No results found. Please try again.")
            return

        first_output = response['outputs'][0]
        if 'outputs' in first_output and first_output['outputs']:
            logger.info(f"Stage 2 response contains output array")
            json_data = first_output['outputs'][0]['results']['text']['data']['text']
            json_match = re.search(r'\`\`\`json\n(.*?)\n\`\`\`', json_data, re.DOTALL)
            logger.info(f"Stage 3 extracted data from triple codes")

            if json_match:
                json_string = json_match.group(1)
                data = json.loads(json_string)
                logger.info(f"Stage 4 prior to extraction of product and recipe data")

                # Handle Recipes and Products
                products, recipes = separate_and_classify_data(data)

                if recipes:
                    logger.info(f"Stage 5 displaying recipes")
                    await cl.Message(content="### Recipes").send()
                    for recipe in recipes:
                        await display_recipe(recipe)

                if products:
                    logger.info(f"Stage 6 displaying product")
                    await cl.Message(content="### Products").send()
                    for product in products:
                        await display_product(product)

                if not recipes and not products:
                    logger.warning("Issue in data received " + str(first_output))
                    await cl.Message(
                        "No recipes or products found for your query. Please try a different search term."
                    ).send()
            else:
                await cl.Message("No results found. Please try again.").send()
        else:
            await cl.Message("No results found. Please try again.").send()

    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        try:
            await cl.Message(f"An error occurred").send()
            logger.info("Sent end of process successfully")
        except Exception as send_error:
            logger.error(f"Failed to send error message: {str(send_error)}")
    finally:
        await temp_msg.remove()

def separate_and_classify_data(data):
    """
    Separate and classify data into products and recipes regardless of input structure.
    Handles cases where the data is a nested dictionary, list, or a single dictionary.
    """
    products = []
    recipes = []

    if isinstance(data, dict):
        # Single dictionary input
        if 'ingredients' in data:
            recipes.append(data)
        elif 'title' in data:  # Check if it's a valid product-like dictionary
            products.append(data)
        else:
            # Nested dictionary with lists
            for key, value in data.items():
                if isinstance(value, list):
                    for item in value:
                        if 'ingredients' in item:
                            recipes.append(item)
                        elif 'title' in item:
                            products.append(item)
                elif isinstance(value, dict):
                    if 'ingredients' in value:
                        recipes.append(value)
                    elif 'title' in value:
                        products.append(value)
    elif isinstance(data, list):
        # Input is a list of dictionaries
        for item in data:
            if 'ingredients' in item:
                recipes.append(item)
            elif 'title' in item:
                products.append(item)

    return products, recipes


async def display_recipe(recipe):
    elements = []
    if 'image_url' in recipe:
        try:
            image_url = recipe['image_url']
            elements.append(cl.Image(name=f"recipe_{recipe['title']}_image", url=image_url))
            logger.info(f"Recipe included image_url {image_url}")
        except Exception as e:
            logger.info(f"Recipe no image_url")
    recipe_url = recipe['url']
    recipe_description = (
        f"**{recipe['title']}**\n"
        f"{recipe['description']}\n\n"
        f"[View Recipe]({recipe_url})"
    )
    logger.info(f"Recipe included title, description and url {recipe_url}")

    if 'video_info' in recipe:
        video_info = recipe['video_info']
        logger.info(f"Recipe get video_info")

        recipe_description += f"\n\n**Video:** {video_info['video_title']}"

        # Use video element with a poster image
        if video_info.get('video_url'):
            video_url = video_info['video_url']
            elements.append(cl.Video(
                name=f"{recipe['title']}_video",
                url=video_url
            ))
            logger.info(f"Recipe included video info {video_url}")

    # Send the main recipe message
    await cl.Message(content=recipe_description, elements=elements).send()
    logger.info(f"Recipe sent title, description, url and video info successfully")

    if 'ingredients' in recipe:
        ingredients_list = "\n".join([f"- {ingredient}" for ingredient in recipe['ingredients']])
        await cl.Message(content=f"**Ingredients:**\n{ingredients_list}").send()
        logger.info(f"Recipe sent ingredients")

    if 'instructions' in recipe:
        instructions_list = "\n".join(
            [f"{i + 1}. {instruction}" for i, instruction in enumerate(recipe['instructions'])]
        )
        await cl.Message(content=f"**Instructions:**\n{instructions_list}").send()
        logger.info(f"Recipe sent instructions")

async def display_product(product):
    elements = []
    try:
        if 'images' in product and product['images']:
            if isinstance(product['images'], str):
                image = product['images']
            else:
                image = product['images'][0]
            elements.append(cl.Image(name=f"product_{product['title']}_image", url=image))
            logger.info(f"Product included images {image}")
        elif 'image' in product and product['image']:
            if isinstance(product['image'], str):
                image = product['image']
            else:
                image = product['image'][0]
            elements.append(cl.Image(name=f"product_{product['title']}_image", url=image))
            logger.info(f"Product included image {image}")
        elif 'image_url' in product:
            if isinstance(product['image_url'], str):
                image = product['image_url']
            else:
                image = product['image_url'][0]
            elements.append(cl.Image(name=f"product_{product['title']}_image", url=image))
            logger.info(f"Product included image url {image}")
    except Exception as e:
        logger.info("Product no image found")
    prd_url = product['url']
    product_description = (
        f"**{product['title']}**\n"
        f"{product['description']}\n\n"
        f"[View Product]({prd_url})"
    )
    logger.info(f"Product included title, description and url {prd_url}")
    if 'price' in product:
        price = product['price']
        product_description += f"\n\n**Price:** ${price}"
        logger.info(f"Product included price {price}")

    await cl.Message(content=product_description, elements=elements).send()
    logger.info(f"Product sent title, description, url, price and image info successfully")

if __name__ == "__main__":
    print("Starting Chainlit application...")
