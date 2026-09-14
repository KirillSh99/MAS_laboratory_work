from thespian.actors import ActorAddress
from agent_base import AgentBase
from messages import MessageType, Message


class TimeAgent(AgentBase):
    def __init__(self):
        super().__init__()
        self.name = ""
        self.count_message = 0

        self.subscribe(MessageType.INITIALIZATION, self.handle_initialization)
        self.subscribe(MessageType.SEND_MESSAGE, self.handle_send_message)
        self.subscribe(MessageType.GET_RESULT, self.handle_get_result)

    def handle_initialization(self, message: Message, sender: ActorAddress):
        print(f'Актор таймер с адресом {self.myAddress} получил {message} от {sender}')
        self.name = message.msg_body.get("name")

    def handle_send_message(self, message: Message, sender: ActorAddress):
        index_message = message.msg_body.get("send_index")
        print(f"Агент TimeAgent: {self.name} получил сообщение от {sender} под номером: {index_message}")

        if index_message >= 0:
            self.count_message += 1

            new_message = Message(
                msg_type=MessageType.SEND_COUNT_MESSAGE_OF_SendAgent,
                msg_body={'count_message': self.count_message,
                          'name_agent': self.name},
            )

            self.send(sender, new_message)

    def handle_get_result(self, message: Message, sender: ActorAddress):
        print(f"Агент TimeAgent: {self.name} получил {self.count_message} обращений")
