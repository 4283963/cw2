"""示例订单与骑手数据，供前端快速加载与 /api/sample 使用。"""
from __future__ import annotations

from typing import Any, Dict, List


def sample_rider() -> Dict[str, Any]:
    return {
        "rider_id": "R-001",
        "location": {"x": 10.0, "y": 10.0},
        "speed": 30.0,  # 单位距离 / 分钟
    }


def sample_orders() -> List[Dict[str, Any]]:
    """返回一组示例订单（含可触发延误风险的场景）。"""
    return [
        {
            "order_id": "O-1001",
            "merchant": {"x": 20.0, "y": 30.0},
            "customer": {"x": 80.0, "y": 70.0},
            "deadline": 6.0,
            "prep_time": 1.0,
            "created_at": 0.0,
        },
        {
            "order_id": "O-1002",
            "merchant": {"x": 40.0, "y": 15.0},
            "customer": {"x": 90.0, "y": 40.0},
            "deadline": 7.0,
            "prep_time": 1.5,
            "created_at": 0.0,
        },
        {
            "order_id": "O-1003",
            "merchant": {"x": 25.0, "y": 60.0},
            "customer": {"x": 70.0, "y": 90.0},
            "deadline": 8.0,
            "prep_time": 0.5,
            "created_at": 0.0,
        },
        {
            "order_id": "O-1004",
            "merchant": {"x": 55.0, "y": 25.0},
            "customer": {"x": 15.0, "y": 85.0},
            "deadline": 9.0,
            "prep_time": 1.0,
            "created_at": 0.0,
        },
    ]


def sample_request() -> Dict[str, Any]:
    return {
        "rider": sample_rider(),
        "orders": sample_orders(),
        "strategy": "min_lateness",
    }
