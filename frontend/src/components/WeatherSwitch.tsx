// 骑手状态切换器：在地图下方切换天气状态。
// 切换到「暴雨天气」时前端把 weather 传给后端，后端会把所有骑手行驶速度减半。
import type { Weather } from '../types'

interface Props {
  weather: Weather
  onChange: (w: Weather) => void
  disabled?: boolean
}

export function WeatherSwitch({ weather, onChange, disabled }: Props) {
  const isStorm = weather === 'storm'
  return (
    <div className={`panel weather-switch ${isStorm ? 'storm' : ''}`}>
      <div className="weather-head">
        <span className="panel-title">骑手状态 / 天气</span>
        {isStorm && <span className="storm-tag">⚠ 暴雨调度告警</span>}
      </div>
      <div className="weather-tabs">
        <button
          className={`wtab ${weather === 'normal' ? 'active' : ''}`}
          disabled={disabled}
          onClick={() => onChange('normal')}
        >
          ☀️ 正常天气
        </button>
        <button
          className={`wtab ${weather === 'storm' ? 'active danger' : ''}`}
          disabled={disabled}
          onClick={() => onChange('storm')}
        >
          ⛈️ 暴雨天气
        </button>
      </div>
      <div className="weather-hint">
        {isStorm
          ? '暴雨模式已生效：所有骑手行驶速度减半，预计超时的订单路线将闪烁红色提醒调度员。'
          : '正常模式：骑手按标准速度配送，预计超时的订单路线仍以红色高亮。'}
      </div>
    </div>
  )
}
