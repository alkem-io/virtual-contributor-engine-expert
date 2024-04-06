import logging
import os
import sys
import io
import glob

from langchain_openai import AzureOpenAIEmbeddings
from config import LOG_LEVEL
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain.vectorstores import FAISS
from langchain.callbacks import get_openai_callback

from config import config, local_path, vectordb_path, chunk_size


logger = logging.getLogger(__name__)
assert LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
logger.setLevel(getattr(logging, LOG_LEVEL))  # Set logger level

# Create handlers
c_handler = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, line_buffering=True))
f_handler = logging.FileHandler(os.path.join(os.path.expanduser(local_path), 'app.log'))

c_handler.setLevel(level=getattr(logging, LOG_LEVEL))
f_handler.setLevel(logging.WARNING)

# Create formatters and add them to handlers
c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%m-%d %H:%M:%S')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%m-%d %H:%M:%S')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

logger.info(f"log level {os.path.basename(__file__)}: {LOG_LEVEL}")

def embed_text(texts, save_loc):
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=config['embeddings_deployment_name'],
        chunk_size=1
    )
    docsearch = FAISS.from_documents(texts, embeddings)
    docsearch.save_local(save_loc)

def load_and_split_texts():
    loader = DirectoryLoader('./data', glob="**/*.txt")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_size/5, length_function=len, is_separator_regex=False)
    texts = text_splitter.split_documents(loader.load())
    return texts

def ingest():
    # open file to check output
    f = open(local_path+"/ingestion_output.txt", "w")
    # Save embeddings to vectordb
    texts = load_and_split_texts()
    with get_openai_callback() as cb:
        embed_text(texts, vectordb_path)
    logger.info(f"\nEmbedding costs: {cb.total_cost}")
    stringified_texts = str(texts)
    f.write(stringified_texts)
    f.close()

    logger.info('ingesting')
    return ''
