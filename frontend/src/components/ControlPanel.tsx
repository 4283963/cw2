// 播放控制面板：播放/暂停/单步/重置、倍速、进度拖动
import type { Frame } from '../types'

interface Props {
  index: number
  total: number
  playing: boolean
  speed: number
  current: Frame | undefined
  onPlay: () => void
  onPause: () => void
  onReset: () => void
  onStepF: () => void
  onStepB: () => void
  onSeek: (i: number) => void
  onSpeed: (s: number) => void
}

export function ControlPanel({
  index,
  total,
  playing,
  speed,
  current,
  onPlay,
  onPause,
  onReset,
  onStepF,
  onStepB,
  onSeek,
  onSpeed,
}: Props) {
  const disabled = total === 0
  const progress = total > 1 ? (index / (total - 1)) * 100 : 0

  return (
    <div className="panel control-panel">
      <div className="ctrl-row">
        <div className="ctrl-buttons">
          <button disabled={disabled} onClick={onReset} title="重置">⏮ 重置</button>
          <button disabled={disabled} onClick={onStepB} title="上一帧">◀</button>
          {playing ? (
            <button className="primary" disabled={disabled} onClick={onPause}>⏸ 暂停</button>
          ) : (
            <button className="primary" disabled={disabled} onClick={onPlay}>▶ 播放</button>
          )}
          <button disabled={disabled} onClick={onStepF} title="下一帧">▶</button>
        </div>

        <div className="ctrl-speed">
          <label>倍速</label>
          <select value={speed} onChange={(e) => onSpeed(Number(e.target.value))}>
            <option value={0.5}>0.5×</option>
            <option value={1}>1×</option>
            <option value={2}>2×</option>
            <option value={4}>4×</option>
            <option value={8}>8×</option>
          </select>
        </div>

        <div className="ctrl-stats">
          <span>时间 <b>{current ? current.t.toFixed(2) : '0.00'}</b> min</span>
          <span>里程 <b>{current ? current.traveled.toFixed(1) : '0.0'}</b></span>
          <span>帧 <b>{index + 1}</b>/{total}</span>
        </div>
      </div>

      <div className="ctrl-progress">
        <input
          type="range"
          min={0}
          max={Math.max(0, total - 1)}
          value={index}
          disabled={disabled}
          onChange={(e) => onSeek(Number(e.target.value))}
        />
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>
    </div>
  )
}
