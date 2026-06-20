// 与后端 api/schemas.py 对应的前端类型定义

export interface Location {
  x: number
  y: number
}

export type StopKind = 'pickup' | 'delivery'
export type OrderState = 'pending' | 'picked' | 'delivered'

export interface Order {
  order_id: string
  merchant: Location
  customer: Location
  deadline: number
  prep_time: number
  created_at: number
}

export interface Rider {
  rider_id: string
  location: Location
  speed: number
}

export interface Stop {
  order_id: string
  kind: StopKind
  location: Location
  arrival_time: number
  departure_time: number
}

export interface RiskItem {
  order_id: string
  predicted_delivery_time: number
  deadline: number
  lateness: number
  margin: number
  is_delay_risk: boolean
  pickup_time: number | null
  sequence_index: number | null
}

export interface RiskAssessment {
  items: RiskItem[]
  risk_count: number
  total_lateness: number
  worst_margin: number
}

export interface FrameEvent {
  order_id: string
  kind: string
  action: string
}

export interface Frame {
  t: number
  x: number
  y: number
  target_order_id: string | null
  target_kind: StopKind | null
  order_states: Record<string, string>
  events: FrameEvent[]
  traveled: number
}

export interface SimulateResult {
  frames: Frame[]
  total_time: number
  total_distance: number
  route: Stop[]
  risk: RiskAssessment
  order_delivery_times: Record<string, number>
  weather: Weather
}

export interface SampleData {
  rider: Rider
  orders: Order[]
  strategy: string
}

export type Strategy = 'min_lateness' | 'min_time'

export type Weather = 'normal' | 'storm'

export interface SimulateRequest {
  rider: Rider
  orders: Order[]
  strategy: Strategy
  max_step: number
  weather: Weather
}
