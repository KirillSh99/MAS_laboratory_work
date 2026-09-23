import logging
from thespian.actors import *
from number_agent import NumberActor
from calculator_actor import CalculatorActor
from message import Message, MessageType


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    actorSystem = ActorSystem()

    calculator_address = actorSystem.createActor(CalculatorActor)

    for i in range(1, 14):
        number_agent = actorSystem.createActor(NumberActor)
        init_message_data = {"init_value": i, "calculator_address": calculator_address}
        init_message = Message(MessageType.INITIALIZATION, init_message_data)
        actorSystem.tell(number_agent, init_message)

    sum_command = Message(MessageType.OPERATION, "SUM_NUMBERS")
    actorSystem.tell(calculator_address, sum_command)
