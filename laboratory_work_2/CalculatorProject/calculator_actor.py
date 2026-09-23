from thespian.actors import ActorAddress
from agent_base import AgentBase
from message import Message, MessageType


class CalculatorActor(AgentBase):
    def __init__(self):
        super().__init__()
        self.values = []
        self.subscribe(MessageType.OPERATION, self.handle_operation)

    def handle_operation(self, message: Message, sender: ActorAddress):
        if isinstance(message.msg_body, dict) and "init_value" in message.msg_body:
            new_value = message.msg_body["init_value"]
            self.values.append(new_value)
            print(
                f"Не вводите больше 10 чисел! Калькулятор не сможет выдать результат! На данный момент вы ввели: {len(self.values)} чисел"
            )
            print(
                f"Актор калькулятора с адресом {self.myAddress} получил {message} от {sender}"
            )

            if len(self.values) > 10:
                print("Калькулятор перегружен! Дальнейшие операции невозможны!")
                self.unsubscribe(MessageType.OPERATION)

        if message.msg_body == "SUM_NUMBERS":
            print(
                "Актор-калькулятор с адресом {} получил {} от {} итоговая сумма: {}".format(
                    self.myAddress, message, sender, sum(self.values)
                )
            )

        elif message.msg_body == "DIFFERENSE_NUMBERS":
            result = self.values[0]
            for v in self.values[1:]:
                result -= v
            print(
                "Актор-калькулятор с адресом {} получил {} от {} итоговая разность: {}".format(
                    self.myAddress, message, sender, result
                )
            )

        elif message.msg_body == "PRODUCTS_NUMBERS":
            result = self.values[0]
            for v in self.values[1:]:
                result *= v
            print(
                "Актор-калькулятор с адресом {} получил {} от {} итоговое произведение: {}".format(
                    self.myAddress, message, sender, result
                )
            )

        elif message.msg_body == "QUOTIENT_NUMBERS":
            result = self.values[0]
            for v in self.values[1:]:
                if v != 0:
                    result /= v
                else:
                    print("Делить на 0 нельзя!")
            print(
                "Актор-калькулятор с адресом {} получил {} от {} итоговое частное: {}".format(
                    self.myAddress, message, sender, result
                )
            )
