import logging
import time

from utils.excel_utils import get_excel_data, save_schedule_to_excel
from agents.scene import Scene
from entities.order_entity import OrderEntity
from entities.couriers_entity import CourierEntity
from agents.agents_dispatcher import AgentsDispatcher


def add_entity(scene, onto_description=None):
    onto_desc = onto_description or {}
    type_input = input("Кого добавить? C - курьер, O - заказ: ").strip().upper()

    if type_input in ("С", "C"):
        existing = scene.get_entities_by_type("COURIER")
        next_num = (
            max((int(c.number) for c in existing if c.number is not None), default=0)
            + 1
        )
        data = {
            "Табельный номер": next_num,
            "ФИО": input("ФИО курьера: ").strip(),
            "Координата начала x": float(input("Координата начала x: ")),
            "Координата начала y": float(input("Координата начала y: ")),
            "Типы заказов": input("Типы заказов (через ';'): ").strip(),
            "Стоимость начала": float(input("Стоимость начала: ")),
            "Стоимость за время": float(input("Стоимость за время: ")),
            "Скорость": float(input("Скорость: ")),
            "Объем ранца": float(input("Объем ранца: ")),
            "Грузоподъемность": float(input("Грузоподъемность: ")),
        }
        return CourierEntity(onto_desc, data, scene)

    if type_input in ("О", "O"):
        existing = scene.get_entities_by_type("ORDER")
        next_num = (
            max((int(o.number) for o in existing if o.number is not None), default=0)
            + 1
        )
        data = {
            "Номер": next_num,
            "Наименование": input("Наименование заказа: ").strip(),
            "Масса": float(input("Масса: ")),
            "Объем": float(input("Объем: ")),
            "Стоимость": float(input("Стоимость: ")),
            "Координата получения x": float(input("Координата получения x: ")),
            "Координата получения y": float(input("Координата получения y: ")),
            "Координата доставки x": float(input("Координата доставки x: ")),
            "Координата доставки y": float(input("Координата доставки y: ")),
            "Время получения заказа": float(input("Время получения заказа: ")),
            "Время доставки заказа": float(input("Время доставки заказа: ")),
            "Тип заказа": input("Тип заказа (например, Обычный / Срочный): ").strip(),
        }
        return OrderEntity(onto_desc, data, scene)

    logging.warning("Неизвестный тип сущности: %s", type_input)
    return None


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    filename = "Исходные данные.xlsx"

    scene = Scene()
    dispatcher = AgentsDispatcher(scene)

    couriers_raw = get_excel_data(filename, "Курьеры")
    for row in couriers_raw:
        courier = CourierEntity({}, row, scene)
        dispatcher.add_entity(courier)

    orders_raw = get_excel_data(filename, "Заказы")
    for row in orders_raw:
        order = OrderEntity({}, row, scene)
        dispatcher.add_entity(order)
    time.sleep(5)

    for courier in scene.get_entities_by_type("COURIER"):
        print(f"\nКурьер: {courier.name}")
        for item in courier.schedule:
            print(
                f"  {item.rec_type}: {item.start_time:.2f} → {item.end_time:.2f}, "
                f"{item.point_from} → {item.point_to}, цена {item.cost:.2f}"
            )

    while True:
        logging.info("A - добавить агента")
        logging.info("D - удалить агента")
        logging.info("U - изменить параметры агента")
        logging.info("L - посмотреть список агентов")
        logging.info("Q - Выход")
        user_input = input(": ").strip().upper()
        was_events_added = False

        if user_input == "Q":
            break
        elif user_input == "A":
            onto_description = {}
            entity = add_entity(scene, onto_description)
            if entity:
                dispatcher.add_entity(entity)
                was_events_added = True
        elif user_input == "D":
            type_input = input("Выберите тип. C - курьер, O - заказ: ").strip().upper()
            name_input = input("Введите имя сущности: ").strip()
            entity_type = "COURIER" if type_input in ("С", "C") else "ORDER"
            was_events_added = dispatcher.remove_entity(entity_type, name_input)
        elif user_input in ("U", "Г"):
            type_input = (
                input("Что изменить? C - скорость курьера, O - окно заказа: ")
                .strip()
                .upper()
            )
            try:
                if type_input in ("С", "C"):
                    name_input = input("ФИО курьера: ").strip()
                    new_vel = float(input("Новая скорость: "))
                    was_events_added = dispatcher.update_courier_velocity(
                        name_input, new_vel
                    )
                elif type_input in ("О", "O"):
                    name_input = input("Наименование заказа: ").strip()
                    new_from = float(input("Новое время получения: "))
                    new_to = float(input("Новое время доставки: "))
                    was_events_added = dispatcher.update_order_window(
                        name_input, new_from, new_to
                    )
            except ValueError as err:
                logging.error("Некорректное число: %s", err)
        elif user_input == "L":
            couriers = scene.get_entities_by_type("COURIER")
            orders = scene.get_entities_by_type("ORDER")
            logging.info(
                "Курьеры: %s",
                [
                    f"{c.name} (типы: {c.types}) (скорость: {c.velocity})"
                    for c in couriers
                ],
            )
            logging.info(
                "Заказы: %s",
                [
                    f"{o.name} (тип: {o.order_type}, курьер: "
                    f"{o.delivery_data.get('courier').name if o.delivery_data.get('courier') else 'не размещён'})"
                    for o in orders
                ],
            )

        if was_events_added:
            time.sleep(0.5)
            new_schedule_records = []
            for courier in scene.get_entities_by_type("COURIER"):
                new_schedule_records.extend(courier.get_schedule_json())
            save_schedule_to_excel(new_schedule_records, "Результаты.xlsx")


if __name__ == "__main__":
    main()
