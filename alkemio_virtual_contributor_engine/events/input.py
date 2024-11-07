class HistoryItem:
    def __init__(self, item: dict):
        self.content = item["content"]
        self.role = item["role"]

    def to_dict(self):
        return {"content": self.content, "role": self.role}


class RoomDetails:
    def __init__(self, details):
        self.room_id = details["roomID"]
        self.thread_id = details["threadID"]
        self.communication_id = details["communicationID"]
        self.interaction_id = details["vcInteractionID"]

    def to_dict(self):
        return {
            "roomID": self.room_id,
            "threadID": self.thread_id,
            "communicationID": self.communication_id,
            "vcInteractionID": self.interaction_id,
        }


class ResultHandler:
    def __init__(self, config):
        self.action = config["action"]
        self.room_details = RoomDetails(config["roomDetails"])

    def to_dict(self):
        return {"action": self.action, "roomDetails": self.room_details.to_dict()}


class Input:
    def __init__(self, input: dict):
        self.engine = input["engine"]
        self.prompt = input["prompt"]
        self.user_id = input["userID"]
        self.message = input["message"]
        self.bok_id = input["bodyOfKnowledgeID"]
        self.context_id = input["contextID"]
        self.history = list(map(lambda item: HistoryItem(item), input["history"]))
        self.external_metadata = input["externalMetadata"]
        self.display_name = input["displayName"]
        self.description = input["description"]
        self.external_config = input["externalConfig"]
        self.result_handler = ResultHandler(input["resultHandler"])
        self.persona_service_id = input["personaServiceID"]

    def to_dict(self):
        return {
            "engine": self.engine,
            "prompt": self.prompt,
            "userID": self.user_id,
            "message": self.message,
            "bodyOfKnowledgeID": self.bok_id,
            "contextID": self.context_id,
            "history": list(map(lambda item: item.to_dict(), self.history)),
            "externalMetadata": self.external_metadata,
            "displayName": self.display_name,
            "description": self.description,
            "externalConfig": self.external_config,
            "resultHandler": self.result_handler.to_dict(),
            "personaServiceID": self.persona_service_id,
        }
