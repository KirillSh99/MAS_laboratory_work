import typing
import logging

from .agent_base import AgentBase
from agents.message import Message, MessageType
from entities.order_entity import OrderEntity


class CourierAgent(AgentBase):

    def __init__(self):
        super().__init__()
        self.name = "Агент курьера"
        self.subscribe(MessageType.PRICE_REQUEST, self.handle_price_request)
        self.subscribe(MessageType.PLANNING_REQUEST, self.handle_planning_request)

    def handle_price_request(self, message, sender):
        order: OrderEntity = message.msg_body
        variants = self.__get_params(order)
        if not variants:
            logging.info(
                "%s — для заказа %s не найдено подходящих вариантов", self.name, order
            )
            return
        v = variants[0]
        logging.info(
            "%s ← PRICE_REQUEST от заказа %s → отвечаю ценой %.2f, окно [%.2f; %.2f]",
            self.name,
            order.name,
            v["price"],
            v["time_from"],
            v["time_to"],
        )
        self.send(sender, Message(MessageType.PRICE_RESPONSE, variants))

    def __get_params(self, order: OrderEntity) -> typing.List[dict]:
        if order.weight > self.entity.max_mass:
            return []
        if order.volume > self.entity.max_volume:
            return []
        params = [self.entity.estimate_order(order)]

        last_point = self.entity.get_last_point()
        distance_to_order = last_point.get_distance_to_other(order.point_from)
        distance_with_order = order.point_from.get_distance_to_other(order.point_to)

        time_to_order = distance_to_order / self.entity.velocity
        time_with_order = distance_with_order / self.entity.velocity

        last_time = self.entity.get_last_time()
        asap_time_from = last_time

        jit_time_from = order.time_from - time_to_order

        if asap_time_from < order.time_from:
            if jit_time_from > 0 and not self.entity.schedule:
                jit_time_to = jit_time_from + time_to_order + time_with_order

                jit_from_variant = {
                    "courier": self.entity,
                    "time_from": jit_time_from,
                    "time_to": jit_time_to,
                    "price": (time_to_order + time_with_order)
                    * self.entity.price_per_time
                    + self.entity.price_start,
                    "order": order,
                    "variant_name": "jit",
                    "move_from": last_time,
                    "move_to": last_time + time_to_order,
                    "move_point_from": last_point,
                    "move_point_to": order.point_from,
                    "wait_from": last_time + time_to_order,
                    "wait_to": jit_time_from,
                    "delivery_from": order.time_from,
                    "delivery_to": jit_time_to,
                }

                params.append(jit_from_variant)

        delivery_time_from = order.time_to - time_to_order - time_with_order

        if delivery_time_from >= last_time and not self.entity.schedule:
            delivery_variant = {
                "courier": self.entity,
                "time_from": delivery_time_from,
                "time_to": order.time_to,
                "price": (time_to_order + time_with_order) * self.entity.price_per_time
                + self.entity.price_start,
                "order": order,
                "variant_name": "jit_delivery",
                "move_from": last_time,
                "move_to": last_time + time_to_order,
                "move_point_from": last_point,
                "move_point_to": order.point_from,
                "wait_from": last_time + time_to_order,
                "wait_to": delivery_time_from,
                "delivery_from": delivery_time_from,
                "delivery_to": order.time_to,
            }

            params.append(delivery_variant)

        return params

    def handle_planning_request(self, message, sender):
        params = message.msg_body
        result = self.entity.add_order_to_schedule(
            params["order"],
            params["time_from"],
            params["time_to"],
            params["price"],
            params,
        )
        status = "принято" if result else "ОТКАЗ (конфликт)"
        logging.info(
            "%s ← PLANNING_REQUEST заказа %s → %s",
            self.name,
            params["order"].name,
            status,
        )
        self.send(sender, Message(MessageType.PLANNING_RESPONSE, result))
