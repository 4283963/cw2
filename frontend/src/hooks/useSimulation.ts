// 离散轨迹动画驱动 Hook：按播放速度逐帧推进骑手动态坐标
import { useCallback, useEffect, useRef, useState } from 'react'
import type { Frame } from '../types'

const BASE_STEP_MS = 90 // 单帧基础间隔（毫秒），speed 为倍率

export function useSimulation(frames: Frame[]) {
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const timerRef = useRef<number | null>(null)

  const total = frames.length

  // 新的帧序列载入时重置进度
  useEffect(() => {
    setIndex(0)
    setPlaying(false)
  }, [frames])

  // 播放定时器
  useEffect(() => {
    if (!playing || total === 0) return
    const stepMs = Math.max(15, BASE_STEP_MS / speed)
    timerRef.current = window.setInterval(() => {
      setIndex((i) => {
        if (i >= total - 1) {
          setPlaying(false)
          return i
        }
        return i + 1
      })
    }, stepMs)
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current)
    }
  }, [playing, speed, total])

  const play = useCallback(() => {
    setIndex((i) => (i >= total - 1 ? 0 : i))
    setPlaying(true)
  }, [total])

  const pause = useCallback(() => setPlaying(false), [])

  const reset = useCallback(() => {
    setPlaying(false)
    setIndex(0)
  }, [])

  const stepForward = useCallback(() => {
    setPlaying(false)
    setIndex((i) => Math.min(i + 1, total - 1))
  }, [total])

  const stepBack = useCallback(() => {
    setPlaying(false)
    setIndex((i) => Math.max(i - 1, 0))
  }, [])

  const seek = useCallback((i: number) => {
    setIndex(Math.max(0, Math.min(i, total - 1)))
  }, [total])

  return {
    index,
    playing,
    speed,
    setSpeed,
    play,
    pause,
    reset,
    stepForward,
    stepBack,
    seek,
    total,
    current: frames[Math.min(index, Math.max(0, total - 1))],
  }
}
