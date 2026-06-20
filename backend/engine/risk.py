"""延误风险评估。

依据调度路线中每笔订单的「预测送达时刻」与「截止时刻」对比，
判定是否为延误风险 (delay risk)。同时附带派件顺序索引、取件时刻等辅助信息，
供前端高亮展示。
"""
from __future__ import annotations

from typing import Dict

from .models import Order, RiskAssessment, RiskItem, ScheduledRoute


def assess_risk(orders, route: ScheduledRoute) -> RiskAssessment:
    items = []
    risk_count = 0
    total_lateness = 0.0
    worst_margin = float("inf")

    # 取件时刻 + 派件顺序索引
    pickup_times: Dict[str, float] = {}
    delivery_index: Dict[str, int] = {}
    seq = 0
    for stop in route.stops:
        if stop.kind == "pickup":
            pickup_times[stop.order_id] = stop.arrival_time
        else:
            delivery_index[stop.order_id] = seq
            seq += 1

    for order in orders:
        predicted = route.order_delivery_times.get(order.order_id)
        if predicted is None:
            predicted = route.total_time  # 未能送达则按总时长计
        lateness = max(0.0, predicted - order.deadline)
        margin = order.deadline - predicted
        is_risk = predicted > order.deadline
        if is_risk:
            risk_count += 1
            total_lateness += lateness
        if margin < worst_margin:
            worst_margin = margin
        items.append(
            RiskItem(
                order_id=order.order_id,
                predicted_delivery_time=predicted,
                deadline=order.deadline,
                lateness=lateness,
                margin=margin,
                is_delay_risk=is_risk,
                pickup_time=pickup_times.get(order.order_id),
                sequence_index=delivery_index.get(order.order_id),
            )
        )

    if worst_margin == float("inf"):
        worst_margin = 0.0

    return RiskAssessment(
        items=items,
        risk_count=risk_count,
        total_lateness=total_lateness,
        worst_margin=worst_margin,
    )
