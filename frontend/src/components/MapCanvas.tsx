// SVG 地图画布：在抽象欧氏坐标平面上绘制商家/顾客/骑手动态坐标与配送路线。
// 暴雨天气下，预计超时订单对应的路线段会闪烁刺眼红色提醒调度员。
import { useMemo } from 'react'
import type { Frame, Order, Rider, RiskItem, Stop, Weather } from '../types'

interface Props {
  orders: Order[]
  rider: Rider
  route: Stop[]
  frames: Frame[]
  index: number
  riskMap: Record<string, RiskItem>
  weather: Weather
}

const W = 900
const H = 600
const PAD = 28

function stateColor(state: string | undefined): string {
  switch (state) {
    case 'delivered':
      return '#22c55e'
    case 'picked':
      return '#f59e0b'
    default:
      return '#64748b'
  }
}

export function MapCanvas({ orders, rider, route, frames, index, riskMap, weather }: Props) {
  const isStorm = weather === 'storm'

  const bounds = useMemo(() => {
    const pts = [rider.location, ...orders.flatMap((o) => [o.merchant, o.customer])]
    const xs = pts.map((p) => p.x)
    const ys = pts.map((p) => p.y)
    let minX = Math.min(...xs)
    let maxX = Math.max(...xs)
    let minY = Math.min(...ys)
    let maxY = Math.max(...ys)
    const spanX = maxX - minX || 1
    const spanY = maxY - minY || 1
    const padX = Math.max(spanX * 0.1, 12)
    const padY = Math.max(spanY * 0.1, 12)
    minX -= padX
    maxX += padX
    minY -= padY
    maxY += padY
    return { minX, maxX, minY, maxY }
  }, [orders, rider])

  const sx = (x: number) =>
    ((x - bounds.minX) / (bounds.maxX - bounds.minX)) * (W - 2 * PAD) + PAD
  const sy = (y: number) =>
    H - (((y - bounds.minY) / (bounds.maxY - bounds.minY)) * (H - 2 * PAD) + PAD)

  const current = frames.length ? frames[Math.min(index, frames.length - 1)] : undefined
  const orderStates = current?.order_states ?? {}

  const riderPos = current
    ? { x: current.x, y: current.y }
    : rider.location

  // 已行驶轨迹
  const trailPts = [
    rider.location,
    ...frames.slice(0, Math.min(index + 1, frames.length)),
  ]
  const trailPath = trailPts.map((p) => `${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`).join(' ')

  // 规划路线按「停靠点」拆成逐段，按该段终点订单是否延误风险着色
  const legs = useMemo(() => {
    const pts = [rider.location, ...route.map((s) => s.location)]
    return route.map((stop, i) => {
      const a = pts[i]
      const b = pts[i + 1]
      const risk = riskMap[stop.order_id]
      return {
        key: `${i}-${stop.order_id}-${stop.kind}`,
        x1: sx(a.x),
        y1: sy(a.y),
        x2: sx(b.x),
        y2: sy(b.y),
        isRisk: !!risk?.is_delay_risk,
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [route, rider, riskMap, bounds])

  // 当前目标连线
  const targetStop =
    current?.target_order_id && current?.target_kind
      ? route.find(
          (s) =>
            s.order_id === current.target_order_id && s.kind === current.target_kind,
        )
      : undefined

  const gridLines = useMemo(() => {
    const step = 10
    const xs: number[] = []
    const ys: number[] = []
    for (let x = Math.ceil(bounds.minX / step) * step; x <= bounds.maxX; x += step)
      xs.push(x)
    for (let y = Math.ceil(bounds.minY / step) * step; y <= bounds.maxY; y += step)
      ys.push(y)
    return { xs, ys }
  }, [bounds])

  // 暴雨雨幕：若干条斜向流动的雨线
  const rainDrops = useMemo(() => {
    const drops: { x: number; y: number; d: number }[] = []
    for (let i = 0; i < 60; i++) {
      drops.push({
        x: Math.random() * W,
        y: Math.random() * H,
        d: 0.6 + Math.random() * 0.8,
      })
    }
    return drops
  }, [isStorm])

  return (
    <div className={`map-wrap ${isStorm ? 'storm' : ''}`}>
      <svg viewBox={`0 0 ${W} ${H}`} className="map-svg" preserveAspectRatio="xMidYMid meet">
        <rect x={0} y={0} width={W} height={H} fill={isStorm ? '#0a1018' : '#0b1220'} />

        {/* 暴雨压暗蒙层 */}
        {isStorm && <rect x={0} y={0} width={W} height={H} fill="#1e3a5f" opacity={0.18} />}

        {/* 网格 */}
        <g stroke="#1e293b" strokeWidth={1}>
          {gridLines.xs.map((x) => (
            <line key={`gx${x}`} x1={sx(x)} y1={PAD} x2={sx(x)} y2={H - PAD} />
          ))}
          {gridLines.ys.map((y) => (
            <line key={`gy${y}`} x1={PAD} y1={sy(y)} x2={W - PAD} y2={sy(y)} />
          ))}
        </g>

        {/* 规划路线：逐段绘制，延误风险段闪烁红色 */}
        {legs.map((lg) => (
          <line
            key={lg.key}
            x1={lg.x1}
            y1={lg.y1}
            x2={lg.x2}
            y2={lg.y2}
            className={`leg ${lg.isRisk ? 'leg-risk' : 'leg-normal'}`}
          />
        ))}

        {/* 已行驶轨迹 */}
        {frames.length > 0 && (
          <polyline
            points={trailPath}
            fill="none"
            stroke="#38bdf8"
            strokeWidth={3}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        )}

        {/* 当前目标连线 */}
        {targetStop && (
          <line
            x1={sx(riderPos.x)}
            y1={sy(riderPos.y)}
            x2={sx(targetStop.location.x)}
            y2={sy(targetStop.location.y)}
            stroke="#fbbf24"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            opacity={0.8}
          />
        )}

        {/* 商家（取件点）- 方块 */}
        {orders.map((o) => {
          const m = o.merchant
          const picked = orderStates[o.order_id] !== 'pending'
          const size = 13
          return (
            <g key={`m-${o.order_id}`} transform={`translate(${sx(m.x)} ${sy(m.y)})`}>
              <rect
                x={-size / 2}
                y={-size / 2}
                width={size}
                height={size}
                rx={2}
                fill={picked ? '#f59e0b' : '#1e293b'}
                stroke="#f59e0b"
                strokeWidth={2}
              />
              <text x={0} y={-size} textAnchor="middle" className="map-label" fill="#fbbf24">
                {o.order_id}·商家
              </text>
            </g>
          )
        })}

        {/* 顾客（派件点）- 圆 */}
        {orders.map((o) => {
          const c = o.customer
          const st = orderStates[o.order_id] ?? 'pending'
          const risk = riskMap[o.order_id]
          const r = 9
          return (
            <g key={`c-${o.order_id}`} transform={`translate(${sx(c.x)} ${sy(c.y)})`}>
              {risk?.is_delay_risk && (
                <circle r={r + 6} fill="none" stroke="#ef4444" strokeWidth={2} opacity={0.85}>
                  <animate attributeName="r" values={`${r + 4};${r + 8};${r + 4}`} dur="1.6s" repeatCount="indefinite" />
                </circle>
              )}
              <circle
                r={r}
                fill={stateColor(st)}
                stroke="#0b1220"
                strokeWidth={2}
              />
              <text x={0} y={r + 14} textAnchor="middle" className="map-label" fill="#e2e8f0">
                {o.order_id}·顾客
              </text>
            </g>
          )
        })}

        {/* 骑手 */}
        <g transform={`translate(${sx(riderPos.x)} ${sy(riderPos.y)})`}>
          <circle r={16} fill="#38bdf8" opacity={0.18}>
            <animate attributeName="r" values="14;22;14" dur="1.8s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.25;0.05;0.25" dur="1.8s" repeatCount="indefinite" />
          </circle>
          <circle r={7} fill="#38bdf8" stroke="#0b1220" strokeWidth={2} />
          <text x={0} y={-16} textAnchor="middle" className="map-label" fill="#7dd3fc" fontWeight={700}>
            🛵 {rider.rider_id}
          </text>
        </g>

        {/* 起点 */}
        <circle cx={sx(rider.location.x)} cy={sy(rider.location.y)} r={4} fill="#94a3b8" />

        {/* 暴雨雨幕（最上层） */}
        {isStorm && (
          <g className="rain-layer">
            {rainDrops.map((d, i) => (
              <line
                key={i}
                x1={d.x}
                y1={d.y}
                x2={d.x - 6}
                y2={d.y + 16}
                stroke="#7dd3fc"
                strokeWidth={1}
                opacity={0.35}
              >
                <animateTransform
                  attributeName="transform"
                  type="translate"
                  values={`0 0; -8 26`}
                  dur={`${d.d}s`}
                  repeatCount="indefinite"
                />
              </line>
            ))}
          </g>
        )}
      </svg>
      <div className="map-legend">
        <span><i className="dot dot-merchant" /> 商家(取件)</span>
        <span><i className="dot dot-customer" /> 顾客(派件)</span>
        <span><i className="dot dot-rider" /> 骑手</span>
        <span><i className="leg-swatch leg-risk" /> 延误风险路线(闪烁)</span>
        <span><i className="leg-swatch leg-normal" /> 正常路线</span>
        <span><i className="dot dot-trail" /> 已行驶轨迹</span>
      </div>
    </div>
  )
}
