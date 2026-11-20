from entities.base_entity import BaseEntity


class WriterEntity(BaseEntity):
    """Сущность Писателя"""

    def __init__(
        self, onto_desc: dict, name: str, id: int, scene=None
    ):
        super().__init__(onto_desc, scene)
        self.name = name
        self.uri = "Writer" + str(id)

    def __repr__(self):
        return "Писатель" + str(self.name)

    def get_type(self):
        return "WRITER"
