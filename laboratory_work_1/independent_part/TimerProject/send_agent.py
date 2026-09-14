from thespian.actors import ActorAddress
from agent_base import AgentBase
from messages import MessageType, Message


class SendAgent(AgentBase):
    def __init__(self):
        super().__init__()
        self.name = ''

        self.subscribe(MessageType.INITIALIZATION, self.handle_initialization)
        self.subscribe(MessageType.COUNT_SEND_MESSAGE, self.handle_count_send_message)
        self.subscribe(MessageType.SEND_COUNT_MESSAGE_OF_SendAgent, self.handle_send_count_message_of_sendagent)

    def handle_initialization(self, message: Message, sender: ActorAddress):
        print(f'Актор отправки с адресом {self.myAddress} получил {message} от {sender}')
        self.name = message.msg_body.get('name')

    def handle_count_send_message(self, message: Message, sender: ActorAddress):
        count_msg = int(message.msg_body.get("count_msg"))
        time_address = message.msg_body.get('time_address')
        print(f"Агент SendAgent получил число: {count_msg} для отправки такого кол-во сообщений TimeAgent: {time_address}")

        for i in range(count_msg):
            new_message = Message(
                msg_type=MessageType.SEND_MESSAGE,
                msg_body={'send_index': i},
            )
            self.send(time_address, new_message)

    def handle_send_count_message_of_sendagent(self, message: Message, sender: ActorAddress):
        count = message.msg_body.get("count_message")
        sender_name = message.msg_body.get("name_agent")

        print(f"Агент SendAgent: {self.name} получил от агента TimeAgent: {sender_name} следующее кол-во обращений: {count}")
