class BaseEntity:
    """Базовая сущность"""

    def __init__(self, onto_desc, scene=None):
        self.onto_description = onto_desc
        self.name = onto_desc.get("data", {}).get("label", {}).get("value")
        self.uri = "UNKNOWN_URI"
        self.scene = scene

    def __repr__(self):
        return "Entity " + str(self.name)

    def get_type(self):
        return "UNKNOWN_TYPE"

    def get_uri(self):
        return self.uri