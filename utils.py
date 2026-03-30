from alkemio_virtual_contributor_engine import query_documents, setup_logger
from alkemio_virtual_contributor_engine import history_as_conversation  # noqa: F401
from alkemio_virtual_contributor_engine import history_as_dict  # noqa: F401

logger = setup_logger(__name__)


def log_docs(docs, purpose):
    if docs and "ids" in docs and docs["ids"] and docs["ids"][0]:
        ids = list(docs["ids"][0])
        logger.info(f"{purpose} documents with ids [{','.join(ids)}] selected")
        logger.debug(f"{purpose} documents: {docs}")


def load_knowledge(query, knowledgeId):
    collection_name = f"{knowledgeId}-knowledge"
    docs = query_documents(query, collection_name, num_docs=4)
    log_docs(docs, "Knowledge")
    return docs
