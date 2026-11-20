import os
import logging
from .base_agent import AgentBase
from .messages import Message, MessageType


class SceneAgent(AgentBase):
    """Класс агента сцены"""

    def __init__(self):
        super().__init__()
        self.name = "Агент сцены"
        self.agent_addresses = {}
        self.entity_registry = {}
        self.dispatcher = None
        self.finish_text = ""
        self.score_mark = 0
        self.draft_text = ""

        self.subscribe(MessageType.REGISTER_DISPATCHER, self.handle_register_dispatcher)
        self.subscribe(MessageType.UPDATE_ENTITY_MESSAGE, self.handle_update_entity)
        self.subscribe(MessageType.REQUEST_USER_SCENE, self.handle_request_user_scene)
        self.subscribe(MessageType.RESPONSE_WRITER_TEXT, self.handle_response_writer_text)
        self.subscribe(MessageType.RESPONSE_EDITOR_TEXT, self.handle_response_editor_text)
        self.subscribe(MessageType.RESPONSE_EXPERT_SCORE, self.handle_response_expert_score)
        self.subscribe(MessageType.CLEAN_DATA, self.handle_clean_data)

    def handle_init_message(self, message, sender):
        msg = message.msg_body or {}

    def handle_register_dispatcher(self, message, sender):
        self.dispatcher = sender
        logging.info(f"{self.name} — зарегистрирован диспетчер: {sender}")

    def handle_update_entity(self, message, sender):
        entity = message.msg_body.get("entity")
        agent_address = message.msg_body.get("agent_address")

        if not entity or not agent_address:
            logging.warning(f"{self} — неполные данные регистрации")
            return

        if not hasattr(entity, "uri"):
            logging.error(f"{self} — сущность без URI")
            return

        logging.info(
            f"{self} — регистрация агента {entity.uri} по адресу {agent_address}"
        )
        self.entity_registry[entity.uri] = entity
        self.agent_addresses[entity.uri] = agent_address

    def handle_request_user_scene(self, message, sender):
        request = message.msg_body.get("request")
        agent_type = message.msg_body.get("agent_type")
        agent_uri = ""

        for uri, entity in self.entity_registry.items():
            if entity.get_type() == agent_type:
                agent_uri = uri
                break

        message_scene = Message(
            MessageType.REQUEST_WRITER_TEXT,
            {
                "request": request,
            },
        )
        for uri, agent_address in self.agent_addresses.items():
            if uri == agent_uri:
                self.send(agent_address, message_scene)
                break

    def handle_response_writer_text(self, message, sender):
        text = message.msg_body.get("writer_result")
        self.draft_text = text
        agent_type = message.msg_body.get("agent_type")
        prompt = message.msg_body.get("prompt")
        agent_uri = ""

        for uri, entity in self.entity_registry.items():
            if entity.get_type() == agent_type:
                agent_uri = uri
                break

        message_scene = Message(
            MessageType.REQUEST_EDITOR_TEXT,
            {
                "text": text,
                "prompt": prompt,
            },
        )

        for uri, agent_address in self.agent_addresses.items():
            if uri == agent_uri:
                self.send(agent_address, message_scene)
                break

    def handle_response_editor_text(self, message, sender):
        text = message.msg_body.get("editor_result")
        agent_type = message.msg_body.get("agent_type")
        prompt = message.msg_body.get("prompt")
        agent_uri = ""

        for uri, entity in self.entity_registry.items():
            if entity.get_type() == agent_type:
                agent_uri = uri
                break

        message_scene = Message(
            MessageType.REQUEST_EXPERT_SCORE,
            {
                "text": text,
                "prompt": prompt,
            },
        )

        for uri, agent_address in self.agent_addresses.items():
            if uri == agent_uri:
                self.send(agent_address, message_scene)
                break

    def handle_response_expert_score(self, message, sender):
        expert_result = message.msg_body.get("expert_result")
        editor_result = message.msg_body.get("editor_result")
        self.set_values(expert_result, editor_result)

        if self.dispatcher:
            final_response = {
                "draft": self.draft_text,
                "edited_text": editor_result,
                "critic_score": expert_result,
                "critic_feedback": "Текст успешно проверен экспертом",
                "logs": ["Сцена отработала полный цикл"]
            }
            message_to_dispatcher = Message(MessageType.RESPONSE_EXPERT_SCORE, final_response)
            self.send(self.dispatcher, message_to_dispatcher)

    def handle_clean_data(self, message, sender):
        logging.info(f"{self.name}: Запрос на очищение данных")
        self.finish_text = ""
        self.score_mark = 0
        self.draft_text = ""

    def set_values(self, expert_result, editor_result):
        self.finish_text = editor_result
        self.score_mark = expert_result

        os.makedirs("result_data", exist_ok=True)

        with open(os.path.join("result_data", "text.txt"), "w", encoding="utf-8") as f:
            f.write(str(self.finish_text))

        with open(os.path.join("result_data", "mark.txt"), "w", encoding="utf-8") as f:
            f.write(str(self.score_mark))

    def get_values(self):
        return self.finish_text, self.score_mark
