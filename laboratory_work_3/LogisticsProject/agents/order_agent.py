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
        self.displaced_count = 0

        self.current_courier = None
        self.current_evaluating_variant = None
        self.pending_consents = []
        self.consent_replies = []

        self.subscribe(MessageType.PRICE_RESPONSE, self.handle_price_response)
        self.subscribe(MessageType.PLANNING_RESPONSE, self.handle_planning_response)
        self.subscribe(MessageType.REMOVE_ORDER, self.handle_remove_message)
        self.subscribe(
            MessageType.DISPLACEMENT_REQUEST, self.handle_displacement_request
        )
        self.subscribe(
            MessageType.DISPLACEMENT_RESPONSE, self.handle_displacement_response
        )
        self.subscribe(MessageType.NEW_COURIER, self.handle_new_resource_message)
        self.subscribe(MessageType.DELETED_COURIER, self.handle_delete_courier_message)
        self.subscribe(MessageType.FREED_SLOT, self.handle_freed_slot_message)
        self.subscribe(MessageType.REPLAN_ORDER, self.handle_replan_message)
        self.subscribe(
            MessageType.UPDATE_ORDER_PARAMS, self.handle_update_params_message
        )

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)
        self.__send_params_request()

    def handle_remove_message(self, message, sender, is_displacement: bool = True):
        courier = message.msg_body
        if is_displacement:
            self.displaced_count += 1
            logging.info(
                "%s — удален из расписания курьера %s. Вытеснен раз: %d",
                self.name,
                courier.name,
                self.displaced_count,
            )
            if self.displaced_count > 3:
                logging.warning(
                    "%s: превышен лимит вытеснений! Заказ снимается с планирования.",
                    self.name,
                )
                self.current_courier = None
                self.entity.delivery_data = {}
                return
        else:
            logging.info(
                "%s — курьер %s выбыл, запускаю перепланирование",
                self.name,
                courier.name,
            )

        self.current_courier = None
        self.entity.delivery_data = {}
        self.current_evaluating_variant = None
        self.possible_variants.clear()
        self.unchecked_couriers.clear()
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

        if best_variant.get("variant_name") == "conflict_multi":
            orders_to_remove = best_variant.get("orders_to_remove", [])
            if orders_to_remove:
                self.pending_consents = []
                self.consent_replies = []
                self.current_evaluating_variant = best_variant

                for ord_ent in orders_to_remove:
                    addr = self.dispatcher.reference_book.get_address(ord_ent)
                    if addr:
                        self.pending_consents.append(addr)
                        self.send(
                            addr, Message(MessageType.DISPLACEMENT_REQUEST, self.entity)
                        )

                if self.pending_consents:
                    logging.info(
                        f"{self.name} запрашивает согласие на вытеснение у {len(self.pending_consents)} заказов."
                    )
                    return

        self._send_planning_request(best_variant)

    def _send_planning_request(self, variant):
        best_variant_address = self.dispatcher.reference_book.get_address(
            variant.get("courier")
        )
        self.current_evaluating_variant = variant

        logging.info(
            f"{self.name} - лучшим признан {variant.get('variant_name')}, запрос курьеру {variant.get('courier').name}"
        )
        request_message = Message(MessageType.PLANNING_REQUEST, variant)
        self.send(best_variant_address, request_message)

    def handle_displacement_request(self, message, sender):
        displacing_order = message.msg_body

        alternatives = []
        if self.current_courier:
            alternatives = [
                v
                for v in self.possible_variants
                if v["courier"].number != self.current_courier.number
            ]

        if alternatives:
            logging.info(
                f"{self.name} СОГЛАСЕН уступить место заказу {displacing_order.name} (есть {len(alternatives)} альт. вариантов)."
            )
            self.send(sender, Message(MessageType.DISPLACEMENT_RESPONSE, True))
        else:
            logging.info(
                f"{self.name} ОТКАЗЫВАЕТ уступить место заказу {displacing_order.name} (нет запасных вариантов)."
            )
            self.send(sender, Message(MessageType.DISPLACEMENT_RESPONSE, False))

    def handle_displacement_response(self, message, sender):
        consent_given = message.msg_body
        if not self.current_evaluating_variant:
            return

        self.consent_replies.append(consent_given)

        if len(self.consent_replies) == len(self.pending_consents):
            if all(self.consent_replies):
                logging.info(
                    f"{self.name} получил согласие ВСЕХ заказов. Отправляем план курьеру!"
                )
                self._send_planning_request(self.current_evaluating_variant)
            else:
                logging.info(
                    f"{self.name} получил ОТКАЗ на вытеснение. Ищу другой вариант."
                )
                if self.current_evaluating_variant in self.possible_variants:
                    self.possible_variants.remove(self.current_evaluating_variant)
                self.current_evaluating_variant = None
                self.__run_planning()

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
            finish_efficiency = self.get_decreasing_kpi_value(
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
            logging.info("%s успешно запланирован", self.name)
            if self.current_evaluating_variant:
                self.current_courier = self.current_evaluating_variant["courier"]
                self.entity.delivery_data = self.current_evaluating_variant
        else:
            logging.warning(
                "%s: Отказ от курьера. Пробуем следующий вариант.", self.name
            )
            if self.current_evaluating_variant in self.possible_variants:
                self.possible_variants.remove(self.current_evaluating_variant)
            self.current_evaluating_variant = None
            self.__run_planning()

    def handle_new_resource_message(self, message, sender):
        courier = message.msg_body
        logging.info("%s — узнал о новом курьере %s", self.name, courier.name)
        if not self.entity.delivery_data.get("courier"):
            self.displaced_count = 0
            self.possible_variants.clear()
            self.unchecked_couriers.clear()
            self.__send_params_request()

    def handle_delete_courier_message(self, message, sender):
        courier = message.msg_body
        if self.entity.delivery_data.get("courier") != courier:
            return
        self.handle_remove_message(message, sender, is_displacement=False)

    def handle_delete_message(self):
        super().handle_delete_message()
        courier = self.entity.delivery_data.get("courier")
        if courier:
            courier_address = self.dispatcher.reference_book.get_address(courier)
            if courier_address:
                payload = {"order": self.entity, "reason": "deleted"}
                self.send(courier_address, Message(MessageType.DELETED_ORDER, payload))
        self.current_courier = None
        self.entity.delivery_data = {}

    def handle_freed_slot_message(self, message, sender):
        courier = message.msg_body
        logging.info(
            "%s — узнал об освобождении времени у курьера %s", self.name, courier.name
        )
        if not self.entity.delivery_data.get("courier") and not self.unchecked_couriers:
            self.displaced_count = 0
            self.possible_variants.clear()
            self.__send_params_request()

    def handle_replan_message(self, message, sender):
        courier = message.msg_body
        logging.info(
            "%s — требуется перепланирование после изменений у курьера %s",
            self.name,
            courier.name,
        )
        self.current_courier = None
        self.entity.delivery_data = {}
        self.current_evaluating_variant = None
        self.possible_variants.clear()
        self.unchecked_couriers.clear()
        self.__send_params_request()

    def handle_update_params_message(self, message, sender):
        data = message.msg_body
        old_window = (self.entity.time_from, self.entity.time_to)
        self.entity.time_from = float(data["time_from"])
        self.entity.time_to = float(data["time_to"])

        logging.info(
            "%s — окно изменено [%.2f; %.2f] → [%.2f; %.2f]",
            self.name,
            old_window[0],
            old_window[1],
            self.entity.time_from,
            self.entity.time_to,
        )

        old_courier = self.entity.delivery_data.get("courier")
        if old_courier:
            courier_address = self.dispatcher.reference_book.get_address(old_courier)
            if courier_address:
                payload = {"order": self.entity, "reason": "replan"}
                self.send(courier_address, Message(MessageType.DELETED_ORDER, payload))

        self.current_courier = None
        self.entity.delivery_data = {}
        self.current_evaluating_variant = None
        self.displaced_count = 0
        self.possible_variants.clear()
        self.unchecked_couriers.clear()
        self.__send_params_request()
