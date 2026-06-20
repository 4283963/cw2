"""Pydantic 请求/响应模型（与引擎 dataclass 解耦，转换在 routes 中完成）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------- 基础 ----------

class LocationSchema(BaseModel):
    x: float
    y: float


class OrderSchema(BaseModel):
    order_id: str
    merchant: LocationSchema
    customer: LocationSchema
    deadline: float = Field(..., description="截止时间（分钟，距开始）")
    prep_time: float = 0.0
    created_at: float = 0.0


class RiderSchema(BaseModel):
    rider_id: str
    location: LocationSchema
    speed: float = Field(..., gt=0, description="单位距离/分钟")


# ---------- 调度 ----------

class ScheduleRequest(BaseModel):
    rider: RiderSchema
    orders: List[OrderSchema]
    strategy: str = Field("min_lateness", description="min_lateness | min_time")


class StopSchema(BaseModel):
    order_id: str
    kind: str
    location: LocationSchema
    arrival_time: float
    departure_time: float


class RiskItemSchema(BaseModel):
    order_id: str
    predicted_delivery_time: float
    deadline: float
    lateness: float
    margin: float
    is_delay_risk: bool
    pickup_time: Optional[float] = None
    sequence_index: Optional[int] = None


class RiskAssessmentSchema(BaseModel):
    items: List[RiskItemSchema]
    risk_count: int
    total_lateness: float
    worst_margin: float


class ScheduleResponse(BaseModel):
    route: List[StopSchema]
    order_delivery_times: Dict[str, float]
    total_time: float
    strategy: str
    risk: RiskAssessmentSchema


# ---------- 模拟 ----------

class SimulateRequest(BaseModel):
    rider: RiderSchema
    orders: List[OrderSchema]
    strategy: str = "min_lateness"
    max_step: float = Field(2.0, gt=0, description="行驶腿相邻帧最大间距")


class FrameSchema(BaseModel):
    t: float
    x: float
    y: float
    target_order_id: Optional[str] = None
    target_kind: Optional[str] = None
    order_states: Dict[str, str] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    traveled: float = 0.0


class SimulateResponse(BaseModel):
    frames: List[FrameSchema]
    total_time: float
    total_distance: float
    route: List[StopSchema]
    risk: RiskAssessmentSchema
    order_delivery_times: Dict[str, float]


# ---------- 示例 ----------

class SampleResponse(BaseModel):
    rider: RiderSchema
    orders: List[OrderSchema]
    strategy: str
