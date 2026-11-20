from collections import defaultdict
import typing


class Scene:
    def __init__(self):
        self.entities = defaultdict(list)

    def get_entities_by_type(self, entity_type) -> typing.List:
        all_entities = self.entities.get(entity_type, [])
        return [entity for entity in all_entities if not entity.is_deleting]
