"""离散轨迹模拟。

依据调度路线 (ScheduledRoute) 中的各停靠点时刻，将骑手行驶过程离散成逐帧快照：
    - 行驶腿用 NumPy linspace 生成中间坐标点，时间按行程时长线性推进；
    - 到达取件/派件点时触发事件并更新订单状态；
    - 商家出餐等待时段插入若干「待机帧」以保持时间连续。
返回 SimulationResult，前端据此逐帧动画化骑手动态坐标。
"""
from __future__ import annotations

import math
from typing import Dict, List

from .geometry import euclidean, interpolate_leg
from .models import (
    Order,
    Rider,
    ScheduledRoute,
    SimulationFrame,
    SimulationResult,
)
from .risk import assess_risk

# 行驶腿相邻帧的最大间距（单位距离），决定动画平滑度
DEFAULT_MAX_STEP = 2.0
# 待机帧的时间步长与上限
DEFAULT_WAIT_DT = 0.5
DEFAULT_MAX_WAIT_FRAMES = 8


def simulate_trajectory(
    orders: List[Order],
    rider: Rider,
    route: ScheduledRoute,
    max_step: float = DEFAULT_MAX_STEP,
    wait_dt: float = DEFAULT_WAIT_DT,
    max_wait_frames: int = DEFAULT_MAX_WAIT_FRAMES,
) -> SimulationResult:
    order_states: Dict[str, str] = {o.order_id: "pending" for o in orders}
    frames: List[SimulationFrame] = []

    t = 0.0
    traveled = 0.0
    pos = rider.location
    prev_depart = 0.0

    def push_frame(x, y, target_id, target_kind, events):
        frames.append(
            SimulationFrame(
                t=round(t, 6),
                x=round(x, 6),
                y=round(y, 6),
                target_order_id=target_id,
                target_kind=target_kind,
                order_states=dict(order_states),
                events=events,
                traveled=round(traveled, 6),
            )
        )

    for stop in route.stops:
        d = euclidean(pos, stop.location)
        travel_time = stop.arrival_time - prev_depart
        if d > 1e-9 and travel_time < 1e-9:
            travel_time = d / rider.speed  # 容错：保证时间与距离一致
        if d <= 1e-9:
            pts = [stop.location]
        else:
            pts = interpolate_leg(pos, stop.location, max_step)
        n = len(pts)
        per = (travel_time / n) if n else 0.0
        seg_d = (d / n) if n else 0.0

        for idx, p in enumerate(pts):
            t += per
            traveled += seg_d
            events = []
            if idx == n - 1:
                action = "picked" if stop.kind == "pickup" else "delivered"
                order_states[stop.order_id] = action
                events.append(
                    {"order_id": stop.order_id, "kind": stop.kind, "action": action}
                )
            push_frame(p.x, p.y, stop.order_id, stop.kind, events)

        pos = stop.location

        # 出餐等待 / 服务时段：插入待机帧保持时间连续
        wait = stop.departure_time - stop.arrival_time
        if wait > 1e-9:
            k = max(1, min(max_wait_frames, int(math.ceil(wait / wait_dt))))
            per_wait = wait / k
            for _ in range(k):
                t += per_wait
                push_frame(pos.x, pos.y, stop.order_id, stop.kind, [])

        prev_depart = stop.departure_time

    if not frames:
        push_frame(pos.x, pos.y, None, None, [])

    risk = assess_risk(orders, route)
    return SimulationResult(
        frames=frames,
        total_time=round(t, 6),
        total_distance=round(traveled, 6),
        route=route,
        risk=risk,
    )
