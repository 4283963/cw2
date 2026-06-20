"""最优配送顺序求解。

问题模型：
    - 骑手从起点出发，需完成 N 笔订单。
    - 每笔订单含两个任务：取件(merchant) 与 派件(customer)，约束取件先于派件。
    - 目标：在取/派件优先约束下，找到一条访问序列使「总延误」最小
      （同时以总耗时作为次级 tie-breaker），从而最小化延误风险。

算法：
    - 订单数 <= EXHAUSTIVE_LIMIT 时：递归枚举所有满足优先约束的可行序列，
      用 Pandas 汇总候选成本后取最优（精确解）。
    - 订单数更大时：采用最近邻贪心 + 邻域交换的启发式（近似解）。
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .geometry import euclidean
from .models import Location, Order, Rider, ScheduledRoute, ScheduledStop

# 单次请求中精确枚举的订单数上限，超过则改用启发式
EXHAUSTIVE_LIMIT = 5

# 每个停靠点的服务耗时（分钟）
SERVICE_PICKUP = 0.5
SERVICE_DELIVERY = 0.5

# tie-breaker 权重：在延误相同时，倾向总耗时更短
TIME_TIE_WEIGHT = 1e-3


def _ready_time(order: Order) -> float:
    """商家出餐就绪时刻 = 订单生成 + 出餐时间。"""
    return order.created_at + order.prep_time


def _evaluate_sequence(
    sequence: List[Tuple[int, str]],
    orders: List[Order],
    rider: Rider,
) -> Tuple[float, float, Dict[int, float]]:
    """评估一条可行序列，返回 (total_time, total_lateness, delivery_times)。"""
    order_by_id = {i: o for i, o in enumerate(orders)}
    prev_loc = rider.location
    t = 0.0
    delivery_times: Dict[int, float] = {}

    for order_idx, kind in sequence:
        order = order_by_id[order_idx]
        target = order.merchant if kind == "pickup" else order.customer
        travel = euclidean(prev_loc, target) / rider.speed
        arrival = t + travel
        if kind == "pickup":
            start = max(arrival, _ready_time(order))
            depart = start + SERVICE_PICKUP
        else:
            depart = arrival + SERVICE_DELIVERY
            delivery_times[order_idx] = arrival
        t = depart
        prev_loc = target

    total_lateness = 0.0
    for idx, order in enumerate(orders):
        dt = delivery_times.get(idx)
        if dt is None:
            continue
        total_lateness += max(0.0, dt - order.deadline)

    return t, total_lateness, delivery_times


def _cost(total_time: float, total_lateness: float, strategy: str) -> float:
    if strategy == "min_time":
        return total_time + TIME_TIE_WEIGHT * total_lateness
    # 默认 min_lateness：先压延误，再用总耗时 tie-break
    return total_lateness + TIME_TIE_WEIGHT * total_time


def _feasible_sequences(n: int) -> List[List[Tuple[int, str]]]:
    """递归生成所有满足「取件先于派件」的可行任务序列。"""
    pickup_done = [False] * n
    delivery_done = [False] * n
    results: List[List[Tuple[int, str]]] = []

    def rec(path: List[Tuple[int, str]]):
        if len(path) == 2 * n:
            results.append(path[:])
            return
        for i in range(n):
            if not pickup_done[i]:
                pickup_done[i] = True
                path.append((i, "pickup"))
                rec(path)
                path.pop()
                pickup_done[i] = False
            elif not delivery_done[i]:
                delivery_done[i] = True
                path.append((i, "delivery"))
                rec(path)
                path.pop()
                delivery_done[i] = False

    rec([])
    return results


def _route_from_sequence(
    sequence: List[Tuple[int, str]],
    orders: List[Order],
    rider: Rider,
    delivery_times: Dict[int, float],
) -> List[ScheduledStop]:
    """把评估过的序列重建为带时刻的停靠点列表。"""
    order_by_id = {i: o for i, o in enumerate(orders)}
    prev_loc = rider.location
    t = 0.0
    stops: List[ScheduledStop] = []

    for order_idx, kind in sequence:
        order = order_by_id[order_idx]
        target = order.merchant if kind == "pickup" else order.customer
        travel = euclidean(prev_loc, target) / rider.speed
        arrival = t + travel
        if kind == "pickup":
            start = max(arrival, _ready_time(order))
            depart = start + SERVICE_PICKUP
        else:
            depart = arrival + SERVICE_DELIVERY
        stops.append(
            ScheduledStop(
                order_id=order.order_id,
                kind=kind,
                location=target,
                arrival_time=arrival,
                departure_time=depart,
            )
        )
        t = depart
        prev_loc = target

    return stops


def _solve_exhaustive(orders: List[Order], rider: Rider, strategy: str) -> List[Tuple[int, str]]:
    """精确枚举 + Pandas 汇总。

    关键设计：
        1. DataFrame **仅存放数值标量列**（全为 float64），序列本身保存在
           独立 Python 列表 (feasible) 中。这彻底避免了把 Python list 塞进
           object dtype 列时引发的隐式标签对齐 / 视图拷贝问题——
           在 uvicorn 多线程执行器下，object 列曾触发 Pandas/NumPy 的
           线程不安全路径导致进程级崩溃。
        2. 用 np.argmin(df["cost"].values) 取得 0-based 位置（语义明确），
           同时映射到 feasible 列表与 DataFrame 行位置，
           完全规避「idxmin 返回行 label 却被当作 iloc position」的错位隐患。
    """
    feasible = _feasible_sequences(len(orders))
    total_times: List[float] = []
    total_lateness: List[float] = []
    costs: List[float] = []
    for seq in feasible:
        tt, tl, _ = _evaluate_sequence(seq, orders, rider)
        total_times.append(tt)
        total_lateness.append(tl)
        costs.append(_cost(tt, tl, strategy))

    df = pd.DataFrame(
        {
            "total_time": total_times,
            "total_lateness": total_lateness,
            "cost": costs,
        },
        index=pd.RangeIndex(len(feasible)),
    )
    # 用 numpy 底层数组求 argmin，返回 0-based 整数位置
    best_pos = int(np.argmin(np.asarray(df["cost"].values)))
    best_seq = feasible[best_pos]
    # 显式释放 DataFrame 与临时列表（高并发下避免内存占用叠加）
    del df, total_times, total_lateness, costs
    # feasible 在函数返回时随栈帧释放
    return best_seq


def _solve_greedy(orders: List[Order], rider: Rider, strategy: str) -> List[Tuple[int, str]]:
    """最近邻贪心 + 2-opt 邻域交换（用于订单较多时）。"""
    n = len(orders)
    pickup_done = [False] * n
    delivery_done = [False] * n
    seq: List[Tuple[int, str]] = []
    prev_loc = rider.location

    for _ in range(2 * n):
        best_task = None
        best_dist = float("inf")
        for i in range(n):
            if not pickup_done[i]:
                d = euclidean(prev_loc, orders[i].merchant)
            elif not delivery_done[i]:
                d = euclidean(prev_loc, orders[i].customer)
            else:
                continue
            if d < best_dist:
                best_dist = d
                best_task = i
        if best_task is None:
            break
        if not pickup_done[best_task]:
            pickup_done[best_task] = True
            seq.append((best_task, "pickup"))
            prev_loc = orders[best_task].merchant
        else:
            delivery_done[best_task] = True
            seq.append((best_task, "delivery"))
            prev_loc = orders[best_task].customer

    # 简单 2-opt 邻域交换改进（在可行域内交换相邻任务）
    improved = True
    ev0 = _evaluate_sequence(seq, orders, rider)
    best_cost = _cost(ev0[0], ev0[1], strategy)
    while improved:
        improved = False
        for i in range(len(seq) - 1):
            cand = seq[:]
            cand[i], cand[i + 1] = cand[i + 1], cand[i]
            # 检查优先约束：取件仍在派件之前
            if not _is_feasible(cand):
                continue
            ev = _evaluate_sequence(cand, orders, rider)
            c = _cost(ev[0], ev[1], strategy)
            if c < best_cost:
                best_cost = c
                seq = cand
                improved = True

    return seq


def _is_feasible(seq: List[Tuple[int, str]]) -> bool:
    seen_pickup = set()
    for idx, kind in seq:
        if kind == "delivery" and idx not in seen_pickup:
            return False
        if kind == "pickup":
            seen_pickup.add(idx)
    return True


def schedule_route(
    orders: List[Order],
    rider: Rider,
    strategy: str = "min_lateness",
) -> ScheduledRoute:
    """计算最优配送顺序并返回调度路线。

    Args:
        orders: 订单列表
        rider: 骑手（含起点与速度）
        strategy: 'min_lateness'（默认，最小化总延误）或 'min_time'（最小化总耗时）
    """
    if not orders:
        return ScheduledRoute(stops=[], total_time=0.0, order_delivery_times={}, strategy=strategy)

    if len(orders) <= EXHAUSTIVE_LIMIT:
        best_seq = _solve_exhaustive(orders, rider, strategy)
    else:
        best_seq = _solve_greedy(orders, rider, strategy)

    total_time, _, delivery_times = _evaluate_sequence(best_seq, orders, rider)
    stops = _route_from_sequence(best_seq, orders, rider, delivery_times)

    order_delivery_times = {orders[idx].order_id: t for idx, t in delivery_times.items()}

    return ScheduledRoute(
        stops=stops,
        total_time=total_time,
        order_delivery_times=order_delivery_times,
        strategy=strategy,
    )
