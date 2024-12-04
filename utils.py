import re
from alkemio_virtual_contributor_engine.events.input import (
    HistoryItem,
    MessageSenderRole,
)
from db_client import DbClient
from models import embed_func
from logger import setup_logger

logger = setup_logger(__name__)


def clear_tags(message):
    return re.sub(r"(-? ?\[@?.*\]\(.*?\))|}|{", "", message).strip()


def entry_as_string(entry: HistoryItem):
    if entry.role == MessageSenderRole.HUMAN:
        return f"Human: {clear_tags(entry.content)}"
    return f"Assistant: {clear_tags(entry.content)}"


def entry_as_message(entry):
    if entry.role == MessageSenderRole.HUMAN:
        return ("human", clear_tags(entry.content))
    return ("assistant", clear_tags(entry.content))


def history_as_text(history: list[HistoryItem]):
    return "\n".join(list(map(entry_as_string, history)))


def history_as_messages(history: list[HistoryItem]):
    return list(map(entry_as_message, history))


def log_docs(docs, purpose):
    if docs:
        ids = list(docs["ids"][0])
        logger.info(f"{purpose} documents with ids [{','.join(ids)}] selected")


def load_context(query, contextId):
    collection_name = f"{contextId}-context"
    docs = load_documents(query, collection_name)
    log_docs(docs, "Context")
    return docs


def load_knowledge(query, knowledgeId):
    collection_name = f"{knowledgeId}-knowledge"
    docs = load_documents(query, collection_name)
    log_docs(docs, "Knowledge")
    return docs


def load_documents(query, collection_name, num_docs=4):
    try:
        db_client = DbClient()
        return db_client.query_docs(query, collection_name, embed_func, num_docs)
    except Exception as inst:
        logger.error(
            f"Error querying collection {collection_name} for question `{query}`"
        )
        logger.exception(inst)
        return {}


def combine_documents(docs, document_separator="\n\n"):
    chunks_array = []
    for index, document in enumerate(docs["documents"][0]):
        chunks_array.append(f"[source:{index}] {document}")

    return document_separator.join(chunks_array)
