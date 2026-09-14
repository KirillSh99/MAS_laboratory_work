from thespian.actors import *
from number_agent import NumberActor
from calculator_actor import CalculatorActor
from message import Message, MessageType


if __name__ == '__main__':
    actorSystem = ActorSystem()

    calculator_address = actorSystem.createActor(CalculatorActor)

    number_agent_1 = actorSystem.createActor(NumberActor)
    init_message_1_data = {'init_value': 1, 'calculator_address': calculator_address}
    init_message_1 = Message(MessageType.INITIALIZATION, init_message_1_data)
    actorSystem.tell(number_agent_1, init_message_1)

    number_agent_2 = actorSystem.createActor(NumberActor)
    init_message_2_data = {'init_value': 3, 'calculator_address': calculator_address}
    init_message_2 = Message(MessageType.INITIALIZATION, init_message_2_data)
    actorSystem.tell(number_agent_2, init_message_2)

    sum_command = Message(MessageType.OPERATION, 'SUM_NUMBERS')
    actorSystem.tell(calculator_address, sum_command)