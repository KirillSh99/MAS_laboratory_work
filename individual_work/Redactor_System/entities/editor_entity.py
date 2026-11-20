from entities.base_entity import BaseEntity


class EditorEntity(BaseEntity):
    """Сущность Проверяющего"""

    def __init__(
            self, onto_desc: dict, name: str, id: int, scene=None
    ):
        super().__init__(onto_desc, scene)
        self.name = name
        self.uri = "Editor" + str(id)

    def __repr__(self):
        return "Проверяющий" + str(self.name)

    def get_type(self):
        return "EDITOR"