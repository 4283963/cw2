// 应用主入口：装配地图、天气切换、控制、统计、订单列表，并驱动模拟请求
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { MapCanvas } from './components/MapCanvas'
import { OrderList } from './components/OrderList'
import { ControlPanel } from './components/ControlPanel'
import { StatsPanel } from './components/StatsPanel'
import { WeatherSwitch } from './components/WeatherSwitch'
import { useSimulation } from './hooks/useSimulation'
import { getSample, runSimulate } from './api/client'
import type { Order, Rider, RiskItem, SimulateResult, Strategy, Stop, Weather } from './types'

export default function App() {
  const [rider, setRider] = useState<Rider | null>(null)
  const [orders, setOrders] = useState<Order[]>([])
  const [strategy, setStrategy] = useState<Strategy>('min_lateness')
  const [maxStep, setMaxStep] = useState(2)
  const [weather, setWeather] = useState<Weather>('normal')
  const [result, setResult] = useState<SimulateResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const didRun = useRef(false)

  useEffect(() => {
    getSample()
      .then((s) => {
        setRider(s.rider)
        setOrders(s.orders)
        setStrategy(s.strategy as Strategy)
      })
      .catch((e) => setError('加载示例失败: ' + String(e)))
  }, [])

  const sim = useSimulation(result?.frames ?? [])

  const riskMap = useMemo<Record<string, RiskItem>>(() => {
    const m: Record<string, RiskItem> = {}
    result?.risk.items.forEach((it) => (m[it.order_id] = it))
    return m
  }, [result])

  const orderDeliveryTimes = result?.order_delivery_times ?? {}

  // 用指定天气触发一次模拟（weather 显式传入，避免闭包陈旧）
  const runWith = useCallback(
    async (w: Weather) => {
      if (!rider) return
      setLoading(true)
      setError(null)
      try {
        const res = await runSimulate({ rider, orders, strategy, max_step: maxStep, weather: w })
        setResult(res)
        didRun.current = true
      } catch (e) {
        setError('模拟失败: ' + String(e))
      } finally {
        setLoading(false)
      }
    },
    [rider, orders, strategy, maxStep],
  )

  // 天气切换后，若已模拟过则自动用新天气重新计算
  useEffect(() => {
    if (didRun.current) runWith(weather)
  }, [weather, runWith])

  const handleRun = () => runWith(weather)

  const routeSequence: Stop[] = result?.route ?? []

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <h1>🛵 外卖骑手动态调度模拟</h1>
          <p>NumPy / Pandas 计算引擎 · FastAPI 树状路由 · React 动态可视化</p>
        </div>
        <div className="config">
          <label>
            调度策略
            <select value={strategy} onChange={(e) => setStrategy(e.target.value as Strategy)}>
              <option value="min_lateness">最小延误</option>
              <option value="min_time">最短耗时</option>
            </select>
          </label>
          <label>
            帧间距
            <input
              type="number"
              min={0.5}
              step={0.5}
              value={maxStep}
              onChange={(e) => setMaxStep(Number(e.target.value))}
            />
          </label>
          <button className="run-btn" disabled={loading || !rider} onClick={handleRun}>
            {loading ? '计算中…' : '▶ 开始模拟'}
          </button>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}
      {!result && !error && (
        <div className="banner info">已加载示例订单，点击「开始模拟」计算最优配送顺序与骑手轨迹。</div>
      )}

      <main className="layout">
        <section className="col-main">
          {rider && (
            <MapCanvas
              orders={orders}
              rider={rider}
              route={routeSequence}
              frames={result?.frames ?? []}
              index={sim.index}
              riskMap={riskMap}
              weather={weather}
            />
          )}
          <WeatherSwitch weather={weather} onChange={setWeather} disabled={loading} />
          {routeSequence.length > 0 && (
            <div className="panel route-strip">
              <span className="panel-title">最优配送顺序</span>
              <div className="route-chain">
                {routeSequence.map((s, i) => (
                  <span key={i} className={`chip chip-${s.kind}`}>
                    {i + 1}. {s.kind === 'pickup' ? '取件' : '派件'} {s.order_id}
                  </span>
                ))}
              </div>
            </div>
          )}
          <ControlPanel
            index={sim.index}
            total={sim.total}
            playing={sim.playing}
            speed={sim.speed}
            current={sim.current}
            onPlay={sim.play}
            onPause={sim.pause}
            onReset={sim.reset}
            onStepF={sim.stepForward}
            onStepB={sim.stepBack}
            onSeek={sim.seek}
            onSpeed={sim.setSpeed}
          />
        </section>

        <aside className="col-side">
          <StatsPanel
            risk={result?.risk ?? null}
            total_time={result?.total_time ?? 0}
            total_distance={result?.total_distance ?? 0}
          />
          <OrderList
            orders={orders}
            riskMap={riskMap}
            orderStates={sim.current?.order_states ?? {}}
            orderDeliveryTimes={orderDeliveryTimes}
          />
        </aside>
      </main>
    </div>
  )
}
