import re


def clear_tags(message):
    return re.sub(r"-? ?\[@?.*\]\(.*?\)", "", message).strip()


def entry_as_message(entry):
    if entry["role"] == "human":
        return "%s: %s" % ("Human", clear_tags(entry["content"]))
    return "%s: %s" % ("Assistant", clear_tags(entry["content"]))


def history_as_messages(history):
    return "\n".join(list(map(entry_as_message, history)))


def combine_documents(docs, document_separator="\n\n"):
    chunks_array = []
    for index, document in enumerate(docs["documents"][0]):
        chunks_array.append("[source:%s] %s" % (index, document))

    return document_separator.join(chunks_array)
