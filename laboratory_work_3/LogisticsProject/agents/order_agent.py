import logging

from .agent_base import AgentBase
from agents.message import Message, MessageType
from utils.planning_config import planning_weights


class OrderAgent(AgentBase):

    def __init__(self):
        super().__init__()
        self.name = "Агент заказа"
        self.possible_variants = []
        self.unchecked_couriers = []

        self.subscribe(MessageType.PRICE_RESPONSE, self.handle_price_response)
        self.subscribe(MessageType.PLANNING_RESPONSE, self.handle_planning_response)

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)
        self.__send_params_request()

    def __send_params_request(self):
        all_couriers = self.scene.get_entities_by_type("COURIER")
        logging.info(
            "%s — список курьеров: %s", self.name, [c.name for c in all_couriers]
        )
        good_courier = []
        for courier in all_couriers:
            if self.entity.order_type not in courier.types:
                logging.info(
                    "%s — типы грузов курьера %s (%s) " "не включают %s",
                    self.name,
                    courier.name,
                    courier.types,
                    self.entity.order_type,
                )
                continue
            point = courier.get_last_point()
            point1 = self.entity.point_from
            distance = point.get_distance_to_other(point1)

            good_courier.append((distance, courier))
        good_courier.sort(key=lambda pair: pair[0])
        good_courier = good_courier[:2]
        logging.info(
            "%s — опрашиваем ближайших: %s",
            self.name,
            [f"{c.name} ({d:.2f})" for d, c in good_courier],
        )
        for distance, courier in good_courier:
            address = self.dispatcher.reference_book.get_address(courier)
            if address is None:
                continue

            logging.info("%s → PRICE_REQUEST курьеру %s", self.name, courier.name)
            self.send(address, Message(MessageType.PRICE_REQUEST, self.entity))
            self.unchecked_couriers.append(address)

    def handle_price_response(self, message, sender):
        variants = message.msg_body
        self.possible_variants.extend(variants)

        if variants:
            v = variants[0]
            logging.info(
                "%s ← PRICE_RESPONSE от %s: цена %.2f, окно [%.2f; %.2f]",
                self.name,
                v["courier"].name,
                v["price"],
                v["time_from"],
                v["time_to"],
            )

        if sender in self.unchecked_couriers:
            self.unchecked_couriers.remove(sender)

        if not self.unchecked_couriers:
            logging.info("%s: все курьеры ответили, выбираю вариант", self.name)
            self.__run_planning()

    def __run_planning(self):
        if not self.possible_variants:
            logging.info(f"{self} - нет возможных вариантов для планирования")
            return

        self.__evaluate_variants()
        sorted_vars = sorted(
            self.possible_variants,
            key=lambda x: x.get("total_efficiency"),
            reverse=True,
        )

        logging.info(f"{self} - {sorted_vars=}")
        best_variant = sorted_vars[0]
        best_variant_address = self.dispatcher.reference_book.get_address(
            best_variant.get("courier")
        )

        logging.info(
            f"{self} - лучшим вариантом признан {best_variant}, "
            f"адрес - {best_variant_address}"
        )

        request_message = Message(MessageType.PLANNING_REQUEST, best_variant)
        self.send(best_variant_address, request_message)

    def __evaluate_variants(self):
        if not self.possible_variants:
            return
        all_start_times = [var.get("time_from") for var in self.possible_variants]
        min_start_time = min(all_start_times)
        max_start_time = max(all_start_times)
        all_finish_times = [var.get("time_to") for var in self.possible_variants]
        min_finish_time = min(all_finish_times)
        max_finish_time = max(all_finish_times)
        all_prices = [var.get("price") for var in self.possible_variants]
        min_price = min(all_prices)
        max_price = max(all_prices)

        for variant in self.possible_variants:
            start_efficiency = self.get_decreasing_kpi_value(
                variant.get("time_from"), min_start_time, max_start_time
            )
            finish_efficiency = self.get_increasing_kpi_value(
                variant.get("time_to"), min_finish_time, max_finish_time
            )
            price_efficiency = self.get_decreasing_kpi_value(
                variant.get("price"), min_price, max_price
            )
            order_price = variant["order"].price
            delivery_price = variant.get("price")

            if order_price > 0:
                cost_efficiency = max(0, min(1, 1 - delivery_price / order_price))
            else:
                cost_efficiency = 0

            variant["start_efficiency"] = start_efficiency
            variant["finish_efficiency"] = finish_efficiency
            variant["price_efficiency"] = price_efficiency
            variant["cost_efficiency"] = cost_efficiency

            variant["total_efficiency"] = (
                planning_weights.finish_weight * finish_efficiency
                + planning_weights.start_weight * start_efficiency
                + planning_weights.price_weight * price_efficiency
                + planning_weights.cost_weight * cost_efficiency
            )

    def handle_planning_response(self, message, sender):
        success = message.msg_body
        if success:
            logging.info("Заказ успешно запланирован")
        else:
            logging.warning("Отказал, вариант невыполним")
