import time
from thespian.actors import ActorAddress
from agent_base import AgentBase
from messages import MessageType, Message


class BlockAgent(AgentBase):
    def __init__(self):
        super().__init__()
        self.name = ''
        self.index_block = 0

        self.subscribe(MessageType.INITIALIZATION, self.handle_initialization)
        self.subscribe(MessageType.NEXT_AGENT, self.handle_next_agent)

    def handle_initialization(self, message: Message, sender: ActorAddress):
        print(f'Актор блок с адресом {self.myAddress} получил {message} от {sender}')
        self.name = message.msg_body.get('name')
        self.index_block = int(self.name[-1]) if len(self.name) == 6 else print(f"Предупреждение! Имя должно содержать 6 символов, в вашем: {len(self.name)}")

    def handle_next_agent(self, message: Message, sender: ActorAddress):
        if self.index_block:
            chain_address = message.msg_body.get("chain_address")
            msg = message.msg_body.get("msg")
            start_time = message.msg_body.get("start_time")
            name = 'ActorSystem' if self.index_block == 1 and len(msg) == 0 else message.msg_body.get('name')
            print(f'{self.name} получил сообщение от {name}')

            new_message = Message(
                msg_type=MessageType.NEXT_AGENT,
                msg_body={
                    'chain_address': chain_address,
                    'msg': msg + f' Сообщение от Block{self.index_block},',
                    'name': self.name,
                    'start_time': start_time,
                },
            )

            if self.index_block == 5:
                self.send(chain_address[0], new_message)
            else:
                if self.index_block == 1:
                    if len(msg) > 0:
                        end_time = time.perf_counter() - start_time
                        print(f'Результат цепочки, представленный агентом {self.name}: {msg}')
                        print(f'Время прохождения сообщения по цепочке: {end_time}')
                    else:
                        self.send(chain_address[self.index_block], new_message)
                else:
                    self.send(chain_address[self.index_block], new_message)
