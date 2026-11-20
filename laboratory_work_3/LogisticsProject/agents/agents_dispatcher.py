import logging
from thespian.actors import ActorSystem, ActorExitRequest

from .reference_book import ReferenceBook
from entities.base_entity import BaseEntity
from agents.message import Message, MessageType
from .order_agent import OrderAgent
from .courier_agent import CourierAgent


TYPES_AGENTS = {
    "ORDER": OrderAgent,
    "COURIER": CourierAgent,
}


class AgentsDispatcher:

    def __init__(self, scene):
        self.actor_system = ActorSystem()
        self.reference_book = ReferenceBook()
        self.scene = scene

    def add_entity(self, entity: BaseEntity) -> bool:
        entity_type = entity.get_type()
        agent_class = TYPES_AGENTS.get(entity_type)
        if not agent_class:
            logging.warning("Для типа %s не указан агент", entity_type)
            return False

        self.scene.entities[entity_type].append(entity)
        self.create_agent(agent_class, entity)
        return True

    def create_agent(self, agent_class, entity):
        agent = self.actor_system.createActor(agent_class)
        self.reference_book.add_agent(entity=entity, agent_address=agent)

        init_data = {
            "dispatcher": self,
            "scene": self.scene,
            "entity": entity,
        }
        self.actor_system.tell(agent, Message(MessageType.INITIALIZATION, init_data))

    def remove_entity(self, entity_type: str, entity_name: str) -> bool:
        entities = self.scene.get_entities_by_type(entity_type)
        for entity in entities:
            if entity.name.strip() == entity_name.strip():
                agent_address = self.reference_book.get_address(entity)
                if not agent_address:
                    logging.error("Агент сущности %s не найден", entity.name)
                    return False
                entity.is_deleting = True
                self.scene.entities[entity_type].remove(entity)
                self.actor_system.tell(agent_address, ActorExitRequest())
                logging.info("Запущено удаление %s: %s", entity_type, entity.name)
                return True

        logging.warning(
            "Сущность %s с именем '%s' не найдена", entity_type, entity_name
        )
        return False

    def update_order_window(
        self, order_name: str, new_time_from: float, new_time_to: float
    ) -> bool:
        if new_time_from > new_time_to:
            logging.error("Время получения не может быть больше времени доставки")
            return False

        for order in self.scene.get_entities_by_type("ORDER"):
            if order.name.strip() == order_name.strip():
                addr = self.reference_book.get_address(order)
                if not addr:
                    logging.error("Агент заказа %s не найден", order.name)
                    return False
                payload = {"time_from": new_time_from, "time_to": new_time_to}
                self.actor_system.tell(
                    addr, Message(MessageType.UPDATE_ORDER_PARAMS, payload)
                )
                return True

        logging.warning("Заказ '%s' не найден", order_name)
        return False

    def update_courier_velocity(self, courier_name: str, new_velocity: float) -> bool:
        if new_velocity <= 0:
            logging.error("Скорость курьера должна быть больше 0")
            return False

        for courier in self.scene.get_entities_by_type("COURIER"):
            if courier.name.strip() == courier_name.strip():
                addr = self.reference_book.get_address(courier)
                if not addr:
                    logging.error("Агент курьера %s не найден", courier.name)
                    return False
                payload = {"velocity": new_velocity}
                self.actor_system.tell(
                    addr, Message(MessageType.UPDATE_COURIER_PARAMS, payload)
                )
                return True

        logging.warning("Курьер '%s' не найден", courier_name)
        return False
