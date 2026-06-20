// 统计面板：关键指标卡片 + 每单「预测送达 vs 截止时间」对比柱状图
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { RiskAssessment } from '../types'

interface Props {
  risk: RiskAssessment | null
  total_time: number
  total_distance: number
}

export function StatsPanel({ risk, total_time, total_distance }: Props) {
  const data =
    risk?.items.map((it) => ({
      name: it.order_id,
      预测送达: Number(it.predicted_delivery_time.toFixed(2)),
      截止时间: Number(it.deadline.toFixed(2)),
      risk: it.is_delay_risk,
    })) ?? []

  const cards = [
    { label: '总耗时', value: `${total_time.toFixed(2)} min`, color: '#38bdf8' },
    { label: '总里程', value: `${total_distance.toFixed(1)}`, color: '#a78bfa' },
    { label: '延误订单', value: `${risk?.risk_count ?? 0}`, color: '#f87171' },
    {
      label: '最差余量',
      value: `${risk ? risk.worst_margin.toFixed(2) : '0.00'} min`,
      color: (risk?.worst_margin ?? 0) < 0 ? '#f87171' : '#4ade80',
    },
  ]

  return (
    <div className="panel stats-panel">
      <div className="panel-title">调度统计</div>
      <div className="stat-cards">
        {cards.map((c) => (
          <div className="stat-card" key={c.label}>
            <div className="stat-label">{c.label}</div>
            <div className="stat-value" style={{ color: c.color }}>
              {c.value}
            </div>
          </div>
        ))}
      </div>

      <div className="chart-title">各订单 预测送达 / 截止时间 对比</div>
      <div className="chart-box">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height={210}>
            <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                contentStyle={{
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: 8,
                  color: '#e2e8f0',
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="预测送达" radius={[3, 3, 0, 0]}>
                {data.map((d, i) => (
                  <Cell key={i} fill={d.risk ? '#ef4444' : '#38bdf8'} />
                ))}
              </Bar>
              <Bar dataKey="截止时间" fill="#64748b" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty">运行模拟后展示图表</div>
        )}
      </div>
    </div>
  )
}
