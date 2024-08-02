import re
from db_client import DbClient
from config import config
from models import chat_llm, condenser_llm, embed_func
from logger import setup_logger

logger = setup_logger(__name__)

logger.info(config)


def clear_tags(message):
    return re.sub(r"-? ?\[@?.*\]\(.*?\)", "", message).strip()


def entry_as_message(entry):
    if entry["role"] == "human":
        return "%s: %s" % ("Human", clear_tags(entry["content"]))
    return "%s: %s" % ("Assistant", clear_tags(entry["content"]))


def history_as_messages(history):
    return "\n".join(list(map(entry_as_message, history)))


def log_docs(purpose, docs):
    if docs:
        ids = list(docs["ids"][0])
        logger.info("%s documents with ids [%s] selected" % (purpose, ",".join(ids)))


def load_context(query, contextId):
    collection_name = "%s-context" % contextId
    docs = load_documents(query, collection_name)
    log_docs(docs, "Context")
    return docs


def load_knowledge(query, knolwedgeId):
    collection_name = "%s-knowledge" % knolwedgeId
    docs = load_documents(query, collection_name)
    log_docs(docs, "Knowledge")
    return docs


def load_documents(query, collection_name, num_docs=4):
    try:
        db_client = DbClient()
        return db_client.query_docs(query, collection_name, num_docs)
    except Exception as inst:
        logger.error(
            "Error querying collection %s for question %s" % (collection_name, query)
        )
        logger.exception(inst)
        return {}


def combine_documents(docs, document_separator="\n\n"):
    chunks_array = []
    for index, document in enumerate(docs["documents"][0]):
        chunks_array.append("[source:%s] %s" % (index, document))

    return document_separator.join(chunks_array)
