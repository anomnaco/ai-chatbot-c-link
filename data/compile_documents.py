
# Add documents to the vectorstore, which is on the database, through an embeddings model
import sys, os
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings, VertexAIEmbeddings
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, ServiceContext, StorageContext
from llama_index.embeddings.langchain import LangchainEmbedding
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.vector_stores.astra_db import AstraDBVectorStore

from integrations.google import init_gcp, GECKO_EMB_DIM
from integrations.openai import OPENAI_EMB_DIM
from pipeline.config import LLMProvider, load_config

dotenv_path = ".env"
load_dotenv(dotenv_path)
astra_db_application_token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
astra_db_api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")


config = load_config("config.yml")

# Provider for LLM
if config.llm_provider == LLMProvider.OpenAI:
    embedding_model = LangchainEmbedding(
        OpenAIEmbeddings(model=config.openai_embeddings_model)
    )
else:
    init_gcp(config)
    embedding_model = LangchainEmbedding(
        VertexAIEmbeddings(model_name=config.google_embeddings_model)
    )

embedding_dimension = (
    OPENAI_EMB_DIM if config.llm_provider == LLMProvider.OpenAI else GECKO_EMB_DIM
)
table_name = ""
if len(sys.argv) < 2 or sys.argv[1] == "output":
    table_name = os.getenv("ASTRA_DB_TABLE_NAME")
elif sys.argv[1] == "ecommerce_sites":
    table_name = os.getenv("ASTRA_DB_TABLE_NAME_ECOMMERCE")
elif sys.argv[1] == "recipe_sites":
    table_name = os.getenv("ASTRA_DB_TABLE_NAME_RECIPE")
elif sys.argv[1] == "video_output":
    table_name = os.getenv("ASTRA_DB_TABLE_NAME_VIDEO")

vectorstore = AstraDBVectorStore(
    token= astra_db_application_token,
    api_endpoint=astra_db_api_endpoint,
    collection_name=table_name,
    embedding_dimension=embedding_dimension,
)

storage_context = StorageContext.from_defaults(vector_store=vectorstore)
service_context = ServiceContext.from_defaults(
    llm=None,
    embed_model=embedding_model,
    node_parser=SimpleNodeParser.from_defaults(
        # According to https://genai.stackexchange.com/questions/317/does-the-length-of-a-token-give-llms-a-preference-for-words-of-certain-lengths
        # tokens are ~4 chars on average, so estimating 1,000 char chunk_size & 500 char overlap as previously used
        chunk_size=1500,
        chunk_overlap=125,
    ),
)


# Perform embedding and add to vectorstore
def add_documents(folder_path):
    documents = SimpleDirectoryReader(folder_path).load_data()
    VectorStoreIndex.from_documents(
        documents=documents,
        storage_context=storage_context,
        service_context=service_context,
        show_progress=True,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "output":
        add_documents("output")
    elif sys.argv[1] == "ecommerce_sites":
        add_documents("ecommerce_sites")
    elif sys.argv[1] == "recipe_sites":
        add_documents("recipes_sites")
    elif sys.argv[1] == "video_output":
        add_documents("video_output")
    else:
        print("Invalid option")
