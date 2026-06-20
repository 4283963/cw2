"""基于 NumPy 的几何工具：欧氏距离、批量距离、离散移动、线段插值。"""
from __future__ import annotations

import numpy as np

from .models import Location


def _to_vec(loc) -> np.ndarray:
    return np.array([loc.x, loc.y], dtype=float)


def euclidean(a: Location, b: Location) -> float:
    """两点欧氏距离（标量）。"""
    diff = _to_vec(a) - _to_vec(b)
    return float(np.hypot(diff[0], diff[1]))


def batch_distance(origins, targets) -> np.ndarray:
    """批量计算欧氏距离。

    Args:
        origins: Location 列表
        targets: Location 列表（长度可与 origins 不同，返回 (m, n) 矩阵）
    """
    o = np.array([_to_vec(p) for p in origins], dtype=float)  # (m, 2)
    t = np.array([_to_vec(p) for p in targets], dtype=float)   # (n, 2)
    # 广播求距离矩阵
    diff = o[:, None, :] - t[None, :, :]
    return np.sqrt((diff ** 2).sum(axis=2))


def move_toward(current: Location, target: Location, step: float) -> Location:
    """从 current 朝 target 移动 step 单位距离，返回新位置。

    若 step 超过剩余距离则抵达 target。
    """
    diff = _to_vec(target) - _to_vec(current)
    dist = float(np.hypot(diff[0], diff[1]))
    if dist <= 1e-9 or step <= 0:
        return Location(float(current.x), float(current.y))
    if step >= dist:
        return Location(float(target.x), float(target.y))
    ratio = step / dist
    moved = _to_vec(current) + diff * ratio
    return Location(float(moved[0]), float(moved[1]))


def interpolate_leg(start: Location, end: Location, max_step: float):
    """用 np.linspace 离散生成一条行驶腿的中间坐标点。

    Args:
        start, end: 起止点
        max_step: 相邻点之间的最大间距（单位距离）
    Returns:
        List[Location]，不包含 start，包含 end。
    """
    diff = _to_vec(end) - _to_vec(start)
    dist = float(np.hypot(diff[0], diff[1]))
    if dist <= 1e-9:
        return [Location(float(end.x), float(end.y))]
    n = max(1, int(np.ceil(dist / max_step)))
    ts = np.linspace(0.0, 1.0, n + 1)[1:]  # 跳过起点
    pts = _to_vec(start)[None, :] + ts[:, None] * diff[None, :]
    return [Location(float(p[0]), float(p[1])) for p in pts]
