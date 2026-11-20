import logging
import typing

from thespian.actors import ActorExitRequest

from .editor_agent import EditorAgent
from .writer_agent import WriterAgent
from .expert_agent import ExpertAgent
from .messages import Message, MessageType
from entities.base_entity import BaseEntity
from entities.editor_entity import EditorEntity
from entities.writer_entity import WriterEntity
from entities.expert_entity import ExpertEntity

from .base_agent import AgentBase

TYPES_AGENTS = {
    "WRITER": WriterAgent,
    "EDITOR": EditorAgent,
    "EXPERT": ExpertAgent,
}


class AgentsDispatcher(AgentBase):
    def __init__(self):
        super().__init__()
        self.scene_agent = None
        self.initialized_agent = 0
        self.api_sender = None

        self.subscribe(MessageType.INIT_DISPATCHER, self.handle_init_dispatcher)
        self.subscribe(MessageType.REQUEST_USER, self.handle_request_user)
        self.subscribe(MessageType.CLEAN_DATA, self.handle_clean_data)
        self.subscribe(MessageType.RESPONSE_EXPERT_SCORE, self.handle_final_result)

    def handle_init_dispatcher(self, message, sender):
        self.scene_agent = message.msg_body["scene_agent_address"]
        self.send(
            self.scene_agent,
            Message(
                MessageType.REGISTER_DISPATCHER,
                {"create_dispatcher": True},
            ),
        )

        onto_description = {}
        writer_entity = WriterEntity(onto_description, "Writer", 1, self.scene_agent)
        editor_entity = EditorEntity(onto_description, "Editor", 1, self.scene_agent)
        expert_entity = ExpertEntity(onto_description, "Expert", 1, self.scene_agent)
        self.add_entity(writer_entity)
        self.add_entity(editor_entity)
        self.add_entity(expert_entity)

    def add_entity(self, entity: BaseEntity):
        entity_type = entity.get_type()
        agent_type = TYPES_AGENTS.get(entity_type)
        if not agent_type:
            logging.warning(f"Для сущности типа {entity_type} не указан агент")
            return False
        self.create_agent(agent_type, entity)
        return True

    def create_agent(self, agent_class, entity):
        agent = self.createActor(agent_class)
        init_data = {
            "dispatcher": self.myAddress,
            "scene_agent_address": self.scene_agent,
            "entity": entity,
        }
        init_message = Message(MessageType.INIT_MESSAGE, init_data)
        self.send(agent, init_message)
        register_msg = Message(
            MessageType.UPDATE_ENTITY_MESSAGE,
            {"entity": entity, "agent_address": agent},
        )
        self.send(self.scene_agent, register_msg)

    def handle_request_user(self, message, sender):
        self.api_sender = sender
        request = message.msg_body.get("request_user")
        logging.info(f"{self.name}: Получен запрос от пользователя: {request}")
        message_dispatcher = Message(
            MessageType.REQUEST_USER_SCENE,
            {
                "request": request,
                "agent_type": "WRITER",
            },
        )
        self.send(self.scene_agent, message_dispatcher)

    def handle_final_result(self, message, sender):
        if self.api_sender:
            self.send(self.api_sender, message.msg_body)
            self.api_sender = None

    def handle_clean_data(self, message, sender):
        logging.info(f"{self.name}: Запрос на очищение данных")
        message_dispatcher = Message(
            MessageType.REQUEST_USER_SCENE,
            {
                "clean": True,
            },
        )
        self.send(self.scene_agent, message_dispatcher)
