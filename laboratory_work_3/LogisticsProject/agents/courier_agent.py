import typing
import logging
import copy

from .agent_base import AgentBase
from agents.message import Message, MessageType
from entities.order_entity import OrderEntity


class CourierAgent(AgentBase):

    def __init__(self):
        super().__init__()
        self.name = "Агент курьера"
        self.subscribe(MessageType.PRICE_REQUEST, self.handle_price_request)
        self.subscribe(MessageType.PLANNING_REQUEST, self.handle_planning_request)
        self.subscribe(MessageType.DELETED_ORDER, self.handle_delete_order_message)
        self.subscribe(
            MessageType.UPDATE_COURIER_PARAMS, self.handle_update_params_message
        )

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)
        all_orders = self.scene.get_entities_by_type("ORDER")
        matched_orders = [
            order for order in all_orders if order.order_type in self.entity.types
        ]
        for order in matched_orders:
            order_address = self.dispatcher.reference_book.get_address(order)
            if order_address:
                new_courier_message = Message(MessageType.NEW_COURIER, self.entity)
                self.send(order_address, new_courier_message)

    def handle_delete_message(self):
        super().handle_delete_message()
        all_orders = self.scene.get_entities_by_type("ORDER")
        for order in all_orders:
            order_address = self.dispatcher.reference_book.get_address(order)
            if order_address:
                deleted_courier_message = Message(
                    MessageType.DELETED_COURIER, self.entity
                )
                self.send(order_address, deleted_courier_message)

    def _notify_unplaced_orders(self, exclude_orders=None):
        exclude = set(exclude_orders or [])
        for order in self.scene.get_entities_by_type("ORDER"):
            if order in exclude:
                continue
            if order.order_type not in self.entity.types:
                continue
            if order.delivery_data.get("courier") is not None:
                continue
            addr = self.dispatcher.reference_book.get_address(order)
            if addr:
                self.send(addr, Message(MessageType.FREED_SLOT, self.entity))

    def handle_delete_order_message(self, message, sender):
        body = message.msg_body
        if isinstance(body, dict):
            order = body["order"]
            reason = body.get("reason", "deleted")
        else:
            order = body
            reason = "deleted"

        order_records = self.entity.get_all_order_records(order)
        if not order_records:
            return

        deleted_start = min(rec.start_time for rec in order_records)

        tail_orders = list(
            dict.fromkeys(
                rec.order
                for rec in self.entity.schedule
                if rec.order is not None
                and rec.order != order
                and rec.start_time >= deleted_start
            )
        )

        orders_to_clear = {order, *tail_orders}
        self.entity.schedule = [
            rec for rec in self.entity.schedule if rec.order not in orders_to_clear
        ]
        logging.info(
            "%s — снят заказ %s (причина: %s), отправлено на перепланирование последующих: %d",
            self.name,
            order.name,
            reason,
            len(tail_orders),
        )

        for tail_order in tail_orders:
            addr = self.dispatcher.reference_book.get_address(tail_order)
            if addr:
                self.send(addr, Message(MessageType.REPLAN_ORDER, self.entity))

        self._notify_unplaced_orders(exclude_orders=orders_to_clear)

    def handle_price_request(self, message, sender):
        order: OrderEntity = message.msg_body
        variants = self.__get_params(order)
        if not variants:
            logging.info(
                "%s — для заказа %s не найдено подходящих вариантов", self.name, order
            )
            self.send(sender, Message(MessageType.PRICE_RESPONSE, []))
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
            if jit_time_from > 0:
                jit_time_to = jit_time_from + time_to_order + time_with_order

                conflicted_records = self.entity.get_conflicts(
                    jit_time_from, jit_time_to
                )

                if not conflicted_records:
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
                else:
                    logging.info(
                        f"{self.name} - обнаружены конфликты {conflicted_records}"
                    )

                    earliest_record = min(
                        conflicted_records, key=lambda x: x.start_time
                    )
                    start_time = earliest_record.start_time
                    start_point = earliest_record.point_from

                    conflicted_distance_to_order = start_point.get_distance_to_other(
                        order.point_from
                    )
                    conflicted_time_to_order = (
                        conflicted_distance_to_order / self.entity.velocity
                    )
                    conflicted_finish = (
                        start_time + conflicted_time_to_order + time_with_order
                    )

                    new_conflicts = self.entity.get_conflicts(
                        start_time, conflicted_finish
                    )
                    orders_to_remove = list(
                        set(
                            [
                                rec.order
                                for rec in new_conflicts
                                if rec.order is not None
                            ]
                        )
                    )

                    total_conflicted_price = sum(o.price for o in orders_to_remove)

                    if (
                        order.price > total_conflicted_price
                        and len(orders_to_remove) > 0
                    ):
                        conflicted_price = (
                            conflicted_time_to_order + time_with_order
                        ) * self.entity.price_per_time + self.entity.price_start

                        conflict_variant = {
                            "courier": self.entity,
                            "time_from": start_time,
                            "time_to": conflicted_finish,
                            "price": conflicted_price,
                            "order": order,
                            "variant_name": "conflict_multi",
                            "orders_to_remove": orders_to_remove,  # Передаем список заказов
                            "move_from": start_time,
                            "move_to": start_time + conflicted_time_to_order,
                            "move_point_from": start_point,
                            "move_point_to": order.point_from,
                            "wait_from": start_time + conflicted_time_to_order,
                            "wait_to": start_time + conflicted_time_to_order,
                            "delivery_from": start_time + conflicted_time_to_order,
                            "delivery_to": conflicted_finish,
                        }
                        params.append(conflict_variant)
                    else:
                        logging.info(
                            f"{self.name} отказ от вытеснения: цена нового ({order.price}) <= сумме старых ({total_conflicted_price})"
                        )

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

    def add_order(self, params: dict) -> bool:
        variant_name = params.get("variant_name")

        if variant_name in ("conflict", "conflict_multi"):
            conflicted_records = self.entity.get_conflicts(
                params.get("time_from"), params.get("time_to")
            )
            conflicted_orders = {
                rec.order for rec in conflicted_records if rec.order is not None
            }

            if variant_name == "conflict_multi":
                expected_orders = set(params.get("orders_to_remove", []))
                if expected_orders and not conflicted_orders.issubset(expected_orders):
                    return False
            elif len(conflicted_orders) > 1:
                return False

            orders_to_remove = list(conflicted_orders)
            old_schedule = copy.copy(self.entity.schedule)

            self.entity.schedule = [
                rec for rec in self.entity.schedule if rec.order not in orders_to_remove
            ]

            adding_result = self.entity.add_order_to_schedule(
                params.get("order"),
                params.get("time_from"),
                params.get("time_to"),
                params.get("price"),
                params,
            )

            if not adding_result:
                self.entity.schedule = old_schedule
            else:
                orders_to_remove.sort(key=lambda x: x.price, reverse=True)
                remove_message = Message(MessageType.REMOVE_ORDER, self.entity)
                for removed_order in orders_to_remove:
                    removed_order_address = self.dispatcher.reference_book.get_address(
                        removed_order
                    )
                    if removed_order_address:
                        self.send(removed_order_address, remove_message)

            return adding_result

        return self.entity.add_order_to_schedule(
            params.get("order"),
            params.get("time_from"),
            params.get("time_to"),
            params.get("price"),
            params,
        )

    def handle_planning_request(self, message, sender):
        params = message.msg_body

        result = self.add_order(params)

        status = "принято" if result else "ОТКАЗ (конфликт)"
        logging.info(
            "%s ← PLANNING_REQUEST заказа %s → %s (вариант: %s)",
            self.name,
            params["order"].name,
            status,
            params.get("variant_name"),
        )
        self.send(sender, Message(MessageType.PLANNING_RESPONSE, result))

    def handle_update_params_message(self, message, sender):
        new_velocity = float(message.msg_body["velocity"])
        old_velocity = self.entity.velocity
        self.entity.velocity = new_velocity

        affected_orders = list(
            dict.fromkeys(
                rec.order for rec in self.entity.schedule if rec.order is not None
            )
        )
        self.entity.schedule.clear()

        logging.info(
            "%s — скорость изменена %.2f → %.2f; перепланируем заказы: %s",
            self.name,
            old_velocity,
            new_velocity,
            [o.name for o in affected_orders],
        )

        affected_orders.sort(key=lambda o: o.price, reverse=True)
        for order in affected_orders:
            addr = self.dispatcher.reference_book.get_address(order)
            if addr:
                self.send(addr, Message(MessageType.REPLAN_ORDER, self.entity))

        if new_velocity > old_velocity:
            self._notify_unplaced_orders(exclude_orders=affected_orders)
