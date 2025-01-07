import chainlit as cl
from langflow_client import LangflowClient
import os
from dotenv import load_dotenv
import json
import logging
import re

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
        response = langflow_client.query(message.content + ". Group them. Provide output in JSON Format")

        if not response or 'outputs' not in response or not response['outputs']:
            await cl.Message("No results found. Please try again.").send()
            return

        first_output = response['outputs'][0]
        if 'outputs' in first_output and first_output['outputs']:
            json_data = first_output['outputs'][0]['results']['text']['data']['text']
            json_match = re.search(r'\`\`\`json\n(.*?)\n\`\`\`', json_data, re.DOTALL)

            if json_match:
                json_string = json_match.group(1)
                data = json.loads(json_string)

                # Handle Recipes and Products
                recipes = data.get('Recipes', []) or data.get('recipes', []) or data.get('Recipe', []) or data.get('recipe', [])
                products = data.get('Products', []) or data.get('products', []) or data.get('Product', []) or data.get('product', [])

                if recipes:
                    await cl.Message(content="### Recipes").send()
                    if isinstance(recipes, dict):
                        await display_recipe(recipes)
                    else:
                        for recipe in recipes:
                            await display_recipe(recipe)

                if products:
                    await cl.Message(content="### Products").send()
                    if isinstance(products, dict):
                        await display_recipe(products)
                    else:
                        for product in products:
                            await display_product(product)

                if not recipes and not products:
                    await cl.Message(
                        "No recipes or products found for your query. Please try a different search term."
                    ).send()
            else:
                await cl.Message("No results found. Please try again.").send()
        else:
            await cl.Message("No results found. Please try again.").send()

    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        await cl.Message(f"An error occurred: {str(e)}").send()
    finally:
        await temp_msg.remove()


async def display_recipe(recipe):
    elements = []
    if 'image_url' in recipe:
        try:
            elements.append(cl.Image(name=f"recipe_{recipe['title']}_image", url=recipe['image_url']))
        except Exception as e:
            pass

    recipe_description = (
        f"**{recipe['title']}**\n"
        f"{recipe['description']}\n\n"
        f"[View Recipe]({recipe['url']})"
    )

    if 'video_info' in recipe:
        video_info = recipe['video_info']
        recipe_description += f"\n\n**Video:** {video_info['video_title']}"

        # Use video element with a poster image
    #     if video_info.get('video_url') and recipe.get('image_url'):
    #         elements.append(cl.Video(
    #             name=f"{recipe['title']}_video",
    #             url=video_info['video_url'],
    #             poster=recipe['image_url']
    #         ))
    #
    # # Send the main recipe message
    # await cl.Message(content=recipe_description, elements=elements).send()
        if video_info.get('video_url'):
            # Use recipe image as thumbnail if available, otherwise try video thumbnail
            thumbnail_url = (
                    recipe.get('image_url') or
                    video_info.get('thumbnail_url') or
                    video_info.get('poster_url')
            )

            if thumbnail_url:
                elements.append(cl.Video(
                    name=f"{recipe['title']}_video",
                    url=video_info['video_url'],
                    poster=thumbnail_url,
                    controls=True,
                    muted=True
                ))
            else:
                # Fallback if no thumbnail is available
                elements.append(cl.Video(
                    name=f"{recipe['title']}_video",
                    url=video_info['video_url'],
                    controls=True,
                    muted=True
                ))

    # Send the main recipe message
    await cl.Message(content=recipe_description, elements=elements).send()

    if 'ingredients' in recipe:
        ingredients_list = "\n".join([f"- {ingredient}" for ingredient in recipe['ingredients']])
        await cl.Message(content=f"**Ingredients:**\n{ingredients_list}").send()

    if 'instructions' in recipe:
        instructions_list = "\n".join(
            [f"{i + 1}. {instruction}" for i, instruction in enumerate(recipe['instructions'])]
        )
        await cl.Message(content=f"**Instructions:**\n{instructions_list}").send()

async def display_product(product):
    elements = []
    try:
        if 'images' in product and product['images']:
            elements.append(cl.Image(name=f"product_{product['title']}_image", url=product['images'][0]))
        elif 'image_url' in product:
            elements.append(cl.Image(name=f"product_{product['title']}_image", url=product['image_url']))
    except Exception as e:
        pass

    product_description = (
        f"**{product['title']}**\n"
        f"{product['description']}\n\n"
        f"[View Product]({product['url']})"
    )

    if 'price' in product:
        product_description += f"\n\n**Price:** ${product['price']}"

    await cl.Message(content=product_description, elements=elements).send()


if __name__ == "__main__":
    print("Starting Chainlit application...")
