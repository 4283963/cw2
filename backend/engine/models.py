"""引擎内部数据模型。

为保证引擎与 Web 层解耦，这里使用轻量 dataclass；Web 层 (api/schemas.py)
使用 Pydantic 模型并在 routes 中做转换。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Location:
    """二维坐标点（与地理坐标系无关的抽象欧氏平面）。"""

    x: float
    y: float

    def as_tuple(self) -> tuple:
        return (self.x, self.y)


@dataclass
class Order:
    """一笔外卖订单。

    Attributes:
        order_id: 订单编号
        merchant: 商家坐标（取件点）
        customer: 顾客坐标（派件点）
        deadline: 截止时间（分钟，距模拟开始的绝对时间）
        prep_time: 商家出餐时间（分钟），骑手需等到该时刻才能取件
        created_at: 订单生成时刻（分钟）
    """

    order_id: str
    merchant: Location
    customer: Location
    deadline: float
    prep_time: float = 0.0
    created_at: float = 0.0


@dataclass
class Rider:
    """骑手。"""

    rider_id: str
    location: Location
    speed: float  # 单位距离 / 分钟


@dataclass
class ScheduledStop:
    """调度路线中的一个停靠点（取件或派件）。"""

    order_id: str
    kind: str  # 'pickup' | 'delivery'
    location: Location
    arrival_time: float
    departure_time: float


@dataclass
class ScheduledRoute:
    """一条完整调度路线。"""

    stops: List[ScheduledStop]
    total_time: float
    order_delivery_times: Dict[str, float] = field(default_factory=dict)
    strategy: str = "min_lateness"


@dataclass
class RiskItem:
    """单笔订单的延误风险评估。"""

    order_id: str
    predicted_delivery_time: float
    deadline: float
    lateness: float
    margin: float  # deadline - delivery_time，负值即超时
    is_delay_risk: bool
    pickup_time: Optional[float] = None
    sequence_index: Optional[int] = None  # 在派件序列中的位置


@dataclass
class RiskAssessment:
    """全部订单的延误风险评估集合。"""

    items: List[RiskItem]
    risk_count: int
    total_lateness: float
    worst_margin: float


@dataclass
class SimulationFrame:
    """模拟的一帧快照（骑手动态坐标 + 订单状态）。"""

    t: float  # 当前时间（分钟）
    x: float
    y: float
    target_order_id: Optional[str]
    target_kind: Optional[str]  # 'pickup' | 'delivery' | None
    order_states: Dict[str, str] = field(default_factory=dict)  # order_id -> pending|picked|delivered
    events: List[Dict[str, str]] = field(default_factory=list)  # [{order_id, kind, action}]
    traveled: float = 0.0


@dataclass
class SimulationResult:
    """完整模拟结果。"""

    frames: List[SimulationFrame]
    total_time: float
    total_distance: float
    route: ScheduledRoute
    risk: RiskAssessment
