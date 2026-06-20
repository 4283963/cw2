"""FastAPI 路由：将 Pydantic 请求转换为引擎模型，调用引擎，再转换为响应。

依赖树：
    routes -> schemas (Pydantic)
           -> engine (models / scheduler / simulator / risk)
           -> data.sample_orders
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter

from data.sample_orders import sample_request
from engine import (
    Location,
    Order,
    Rider,
    assess_risk,
    schedule_route,
    simulate_trajectory,
)
from .schemas import (
    FrameSchema,
    LocationSchema,
    OrderSchema,
    RiderSchema,
    RiskAssessmentSchema,
    RiskItemSchema,
    SampleResponse,
    ScheduleRequest,
    ScheduleResponse,
    SimulateRequest,
    SimulateResponse,
    StopSchema,
)

router = APIRouter(prefix="/api", tags=["dispatch"])


# ---------- 转换函数 ----------

def _to_location(loc: LocationSchema) -> Location:
    return Location(x=loc.x, y=loc.y)


def _to_order(o: OrderSchema) -> Order:
    return Order(
        order_id=o.order_id,
        merchant=_to_location(o.merchant),
        customer=_to_location(o.customer),
        deadline=o.deadline,
        prep_time=o.prep_time,
        created_at=o.created_at,
    )


def _to_rider(r: RiderSchema) -> Rider:
    return Rider(
        rider_id=r.rider_id,
        location=_to_location(r.location),
        speed=r.speed,
    )


def _to_stop_schema(stop) -> StopSchema:
    return StopSchema(
        order_id=stop.order_id,
        kind=stop.kind,
        location=LocationSchema(x=stop.location.x, y=stop.location.y),
        arrival_time=stop.arrival_time,
        departure_time=stop.departure_time,
    )


def _to_risk_schema(risk) -> RiskAssessmentSchema:
    items = [
        RiskItemSchema(
            order_id=it.order_id,
            predicted_delivery_time=it.predicted_delivery_time,
            deadline=it.deadline,
            lateness=it.lateness,
            margin=it.margin,
            is_delay_risk=it.is_delay_risk,
            pickup_time=it.pickup_time,
            sequence_index=it.sequence_index,
        )
        for it in risk.items
    ]
    return RiskAssessmentSchema(
        items=items,
        risk_count=risk.risk_count,
        total_lateness=risk.total_lateness,
        worst_margin=risk.worst_margin,
    )


def _orders_from_request(req) -> List[Order]:
    return [_to_order(o) for o in req.orders]


def _apply_weather(rider: Rider, weather: str) -> Rider:
    """根据天气调整骑手行驶速度：暴雨天气所有骑手速度减半。"""
    if weather == "storm":
        return Rider(
            rider_id=rider.rider_id,
            location=rider.location,
            speed=rider.speed / 2.0,
        )
    return rider


# ---------- 端点 ----------

@router.get("/health")
def health():
    return {"status": "ok", "engine": "numpy+pandas+fastapi"}


@router.get("/sample", response_model=SampleResponse)
def get_sample():
    data = sample_request()
    return SampleResponse(**data)


@router.post("/schedule", response_model=ScheduleResponse)
def post_schedule(req: ScheduleRequest):
    orders = _orders_from_request(req)
    rider = _apply_weather(_to_rider(req.rider), req.weather)
    route = schedule_route(orders, rider, strategy=req.strategy)
    risk = assess_risk(orders, route)
    return ScheduleResponse(
        route=[_to_stop_schema(s) for s in route.stops],
        order_delivery_times=route.order_delivery_times,
        total_time=route.total_time,
        strategy=route.strategy,
        risk=_to_risk_schema(risk),
        weather=req.weather,
    )


@router.post("/simulate", response_model=SimulateResponse)
def post_simulate(req: SimulateRequest):
    orders = _orders_from_request(req)
    rider = _apply_weather(_to_rider(req.rider), req.weather)
    route = schedule_route(orders, rider, strategy=req.strategy)
    result = simulate_trajectory(orders, rider, route, max_step=req.max_step)
    frames = [
        FrameSchema(
            t=f.t,
            x=f.x,
            y=f.y,
            target_order_id=f.target_order_id,
            target_kind=f.target_kind,
            order_states=f.order_states,
            events=f.events,
            traveled=f.traveled,
        )
        for f in result.frames
    ]
    return SimulateResponse(
        frames=frames,
        total_time=result.total_time,
        total_distance=result.total_distance,
        route=[_to_stop_schema(s) for s in route.stops],
        risk=_to_risk_schema(result.risk),
        order_delivery_times=route.order_delivery_times,
        weather=req.weather,
    )
