class Source:

    def __init__(self, source):
        self.chunk_index = None
        self.embedding_type = None

        if "chunkIndex" in source:
            self.chunk_index = source["chunkIndex"]

        if "embeddingTtype" in source:
            self.embedding_type = source.get("embeddingType")

        self.document_id = source["documentId"]
        self.source = source["source"]
        self.title = source["title"]
        self.type = source["type"]
        self.score = source["score"]
        self.uri = source["uri"]

    def to_dict(self):
        result = {
            "documentId": self.document_id,
            "source": self.source,
            "title": self.title,
            "type": self.type,
            "score": self.score,
            "uri": self.uri,
        }

        if self.chunk_index:
            result["chunkIndex"] = self.chunk_index
        if self.embedding_type:
            result["embeddingType"] = self.embedding_type
        return result


class Response:

    def __init__(self, response=None):
        if response is not None:
            self.result = response["result"]
            self.human_language = response["human_language"]
            self.result_language = response["result_language"]
            self.knowledge_language = response["knowledge_language"]
            self.original_result = response["original_result"]
            self.sources = list(map(lambda source: Source(source), response["sources"]))

    def to_dict(self):
        return {
            "result": self.result,
            "humanLanguage": self.human_language,
            "resultLanguage": self.result_language,
            "knowledgeLanguage": self.knowledge_language,
            "originalResult": self.original_result,
            "sources": list(map(lambda source: source.to_dict(), self.sources)),
        }
