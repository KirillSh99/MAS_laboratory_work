from thespian.actors import *


class NumberActor(Actor):
    def __init__(self):
        super().__init__()
        self.value = 0

    def receiveMessage(self, msg, sender):
        print(f'Актор числа с адресом {self.myAddress} получил {msg} от {sender}')
        self.value = msg.get('init_value')
        calculator_address = msg.get('calculator_address')
        self.send(calculator_address, self.value)


class CalculatorActor(Actor):
    def __init__(self):
        super().__init__()
        self.values = []

    def receiveMessage(self, msg, sender):
        self.values.append(msg)
        total_sum = sum(self.values)
        print(f'Актор-калькулятор с адресом {self.myAddress} получил {msg} от {sender}, '
              f'итоговая сумма: {total_sum}')


if __name__ == "__main__":
    actorSystem = ActorSystem()
    calculator_address = actorSystem.createActor(CalculatorActor)

    number_agent_1 = actorSystem.createActor(NumberActor)
    init_message_1 = {'init_value': 1, 'calculator_address': calculator_address}
    actorSystem.tell(number_agent_1, init_message_1)

    number_agent_2 = actorSystem.createActor(NumberActor)
    init_message_2 = {'init_value': 2, 'calculator_address': calculator_address}
    actorSystem.tell(number_agent_2, init_message_2)

    number_agent_3 = actorSystem.createActor(NumberActor)
    init_message_3 = {'init_value': 3, 'calculator_address': calculator_address}
    actorSystem.tell(number_agent_3, init_message_3)
