import chromadb
from config import config
from logger import setup_logger

logger = setup_logger(__name__)


class DbClient(object):
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=config["db_host"], port=config["db_port"]
        )

    def __new__(cls):
        if not hasattr(cls, "instance"):
            try:
                cls.instance = super(DbClient, cls).__new__(cls)
            except Exception as inst:
                logger.error("Error connecting to vector db.")
                logger.exception(inst)

        return cls.instance

    def query_docs(self, query, collection, embed_func, num_docs=4):
        collection = self.client.get_collection(
            collection, embedding_function=embed_func
        )

        return collection.query(
            query_texts=[query], include=["documents", "metadatas"], n_results=num_docs
        )
