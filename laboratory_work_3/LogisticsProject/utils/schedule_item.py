from dataclasses import dataclass
from entities.order_entity import OrderEntity
from point import Point


@dataclass
class ScheduleItem:
    order: OrderEntity
    rec_type: str
    start_time: int
    end_time: int
    point_from: Point
    point_to: Point
    cost: float
    all_params: dict
