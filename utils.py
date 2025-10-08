from alkemio_virtual_contributor_engine.chromadb_client import chromadb_client
from models import embed_func
from logger import setup_logger

from alkemio_virtual_contributor_engine.events.input import (
    HistoryItem,
)
from alkemio_virtual_contributor_engine.utils import (
    clear_tags
)

logger = setup_logger(__name__)

def log_docs(docs, purpose):
    if docs:
        ids = list(docs["ids"][0])
        logger.info(f"{purpose} documents with ids [{','.join(ids)}] selected")

def history_as_conversation(history: list[HistoryItem]):
    return "\n".join(list(map(lambda message: f"{message.role}: {clear_tags(message.content)}", history)))

def history_as_dict(history: list[HistoryItem]):
    return list(
        map(
            lambda history_item: {"role": history_item.role, "content": clear_tags(history_item.content)},
            history
        )
    )


# def load_context(query, contextId):
#     collection_name = f"{contextId}-context"
#     docs = load_documents(query, collection_name)
#     log_docs(docs, "Context")
#     return docs
#

def load_knowledge(query, knowledgeId):
    collection_name = f"{knowledgeId}-knowledge"
    docs = load_documents(query, collection_name)
    log_docs(docs, "Knowledge")
    return docs


def load_documents(query, collection_name, num_docs=4):
    try:
        collection = chromadb_client.get_collection(
            collection_name, embedding_function=embed_func
        )
        return collection.query(query_texts=[query], n_results=num_docs)
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
