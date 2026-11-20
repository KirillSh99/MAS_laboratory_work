from entities.base_entity import BaseEntity


class ExpertEntity(BaseEntity):
    """Сущность Эксперта"""

    def __init__(
            self, onto_desc: dict, name: str, id: int, scene=None
    ):
        super().__init__(onto_desc, scene)
        self.name = name
        self.uri = "Expert" + str(id)

    def __repr__(self):
        return "Эксперт" + str(self.name)

    def get_type(self):
        return "EXPERT"