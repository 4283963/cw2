// 订单列表：实时显示每笔订单的状态、预测送达、截止、延误风险
import type { Order, RiskItem } from '../types'

interface Props {
  orders: Order[]
  riskMap: Record<string, RiskItem>
  orderStates: Record<string, string>
  orderDeliveryTimes: Record<string, number>
}

const STATE_LABEL: Record<string, string> = {
  pending: '待取件',
  picked: '配送中',
  delivered: '已送达',
}

function stateClass(state: string): string {
  return `state state-${state}`
}

export function OrderList({ orders, riskMap, orderStates, orderDeliveryTimes }: Props) {
  return (
    <div className="panel order-list">
      <div className="panel-title">订单与延误风险</div>
      <div className="orders">
        {orders.map((o) => {
          const risk = riskMap[o.order_id]
          const state = orderStates[o.order_id] ?? 'pending'
          const predicted = orderDeliveryTimes[o.order_id] ?? risk?.predicted_delivery_time ?? 0
          return (
            <div key={o.order_id} className={`order-card ${risk?.is_delay_risk ? 'risk' : ''}`}>
              <div className="order-head">
                <span className="order-id">{o.order_id}</span>
                <span className={stateClass(state)}>{STATE_LABEL[state] ?? state}</span>
              </div>
              <div className="order-meta">
                <div>派件序位：第 {(risk?.sequence_index ?? 0) + 1} 位</div>
                <div>截止时间：<b>{o.deadline.toFixed(1)}</b> min</div>
                <div>预测送达：<b>{predicted.toFixed(2)}</b> min</div>
                <div>
                  时间余量：
                  <b style={{ color: (risk?.margin ?? 0) < 0 ? '#f87171' : '#4ade80' }}>
                    {risk ? (risk.margin >= 0 ? '+' : '') + risk.margin.toFixed(2) : '—'} min
                  </b>
                </div>
              </div>
              {risk?.is_delay_risk && (
                <div className="risk-badge">⚠ 延误风险（超时 {risk.lateness.toFixed(2)} min）</div>
              )}
              <div className="order-locs">
                商家({o.merchant.x.toFixed(0)},{o.merchant.y.toFixed(0)}) →
                顾客({o.customer.x.toFixed(0)},{o.customer.y.toFixed(0)})
              </div>
            </div>
          )
        })}
        {orders.length === 0 && <div className="empty">暂无订单</div>}
      </div>
    </div>
  )
}
