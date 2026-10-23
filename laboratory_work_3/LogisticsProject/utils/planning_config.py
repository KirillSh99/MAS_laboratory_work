from dataclasses import dataclass


@dataclass
class PlanningWeights:
    finish_weight: float = 0.25
    start_weight: float = 0.15
    price_weight: float = 0.40
    cost_weight: float = 0.20


planning_weights = PlanningWeights()
