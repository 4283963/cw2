"""外卖配送调度模拟 - 计算引擎包。

本包对外暴露四个核心能力：
    - geometry     : 基于 NumPy 的欧氏距离与离散移动
    - scheduler    : 最优配送顺序求解（带取件/派件优先约束）
    - simulator    : 骑手离散轨迹模拟（逐帧推进）
    - risk         : 延误风险评估

模块间采用树状依赖：
    scheduler -> geometry
    simulator -> geometry
    risk      -> models
    api       -> scheduler / simulator / risk
"""
from .models import (  # noqa: F401
    Location,
    Order,
    Rider,
    ScheduledStop,
    ScheduledRoute,
    RiskItem,
    RiskAssessment,
    SimulationFrame,
    SimulationResult,
)
from .geometry import euclidean, batch_distance, move_toward, interpolate_leg  # noqa: F401
from .scheduler import schedule_route  # noqa: F401
from .simulator import simulate_trajectory  # noqa: F401
from .risk import assess_risk  # noqa: F401
