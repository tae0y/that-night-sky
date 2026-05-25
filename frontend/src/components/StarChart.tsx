import { useEffect, useRef, useState } from 'react'
import type { SkyData } from '../types'

interface Props {
  skyData: SkyData
}

const VIEW_W = 2
const VIEW_H = 1
const ZOOM_MIN = 0.25
const ZOOM_MAX = 8

function starRadius(mag: number): number {
  const clamped = Math.max(0, Math.min(6, mag))
  return 0.018 - clamped * (0.018 - 0.0018) / 6
}

function starOpacity(mag: number): number {
  return Math.max(0.35, Math.min(1.0, 1 - mag / 8))
}

export function StarChart({ skyData }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [zoom, setZoom] = useState(1)
  const [tx, setTx] = useState(0)
  const [ty, setTy] = useState(0)
  const dragStart = useRef<{ mx: number; my: number; tx: number; ty: number } | null>(null)
  const pinchRef = useRef<number | null>(null)

  // Auto-rotate: 1 full revolution per 10 min → 0.6 deg/s → ~0.01 deg per frame
  const angleRef = useRef(0)
  const rafRef = useRef<number>(0)
  const lastTimeRef = useRef<number | null>(null)

  useEffect(() => {
    const step = (now: number) => {
      if (lastTimeRef.current === null) lastTimeRef.current = now
      const dt = now - lastTimeRef.current
      lastTimeRef.current = now
      angleRef.current = (angleRef.current + (dt / 1000) * 0.6) % 360
      if (svgRef.current) {
        const g = svgRef.current.querySelector<SVGGElement>('#chart-group')
        if (g) {
          g.setAttribute(
            'transform',
            `rotate(${angleRef.current} 0 1) translate(${tx} ${ty}) scale(${zoom})`,
          )
        }
      }
      rafRef.current = requestAnimationFrame(step)
    }
    rafRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(rafRef.current)
  }, [tx, ty, zoom])

  function resetView() {
    setZoom(1)
    setTx(0)
    setTy(0)
    angleRef.current = 0
  }

  function onWheel(e: React.WheelEvent) {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.85 : 1.18
    setZoom(z => Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, z * delta)))
  }

  function onMouseDown(e: React.MouseEvent) {
    dragStart.current = { mx: e.clientX, my: e.clientY, tx, ty }
  }
  function onMouseMove(e: React.MouseEvent) {
    if (!dragStart.current) return
    const dx = (e.clientX - dragStart.current.mx) * 0.002
    const dy = (e.clientY - dragStart.current.my) * 0.002
    setTx(dragStart.current.tx + dx)
    setTy(dragStart.current.ty + dy)
  }
  function onMouseUp() { dragStart.current = null }

  function onTouchStart(e: React.TouchEvent) {
    if (e.touches.length === 1) {
      dragStart.current = { mx: e.touches[0].clientX, my: e.touches[0].clientY, tx, ty }
      pinchRef.current = null
    } else if (e.touches.length === 2) {
      const dx = e.touches[0].clientX - e.touches[1].clientX
      const dy = e.touches[0].clientY - e.touches[1].clientY
      pinchRef.current = Math.hypot(dx, dy)
      dragStart.current = null
    }
  }
  function onTouchMove(e: React.TouchEvent) {
    e.preventDefault()
    if (e.touches.length === 1 && dragStart.current) {
      const dx = (e.touches[0].clientX - dragStart.current.mx) * 0.002
      const dy = (e.touches[0].clientY - dragStart.current.my) * 0.002
      setTx(dragStart.current.tx + dx)
      setTy(dragStart.current.ty + dy)
    } else if (e.touches.length === 2 && pinchRef.current !== null) {
      const dx = e.touches[0].clientX - e.touches[1].clientX
      const dy = e.touches[0].clientY - e.touches[1].clientY
      const dist = Math.hypot(dx, dy)
      const factor = dist / pinchRef.current
      pinchRef.current = dist
      setZoom(z => Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, z * factor)))
    }
  }
  function onTouchEnd() { dragStart.current = null; pinchRef.current = null }

  const { stars, constellation_lines } = skyData
  const hipToPos = new Map(stars.map(s => [s.hip, s]))

  return (
    <div data-testid="star-chart" className="w-full h-full relative select-none">
      <svg
        ref={svgRef}
        viewBox={`-1 0 ${VIEW_W} ${VIEW_H}`}
        preserveAspectRatio="xMidYMid meet"
        className="w-full h-full"
        style={{ background: '#0a0a12' }}
        onWheel={onWheel}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        <defs>
          {/* 10 shared radial gradients for star glow */}
          {Array.from({ length: 10 }, (_, i) => (
            <radialGradient key={i} id={`sg${i}`} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity={1 - i * 0.08} />
              <stop offset="100%" stopColor="#c9a84c" stopOpacity={0} />
            </radialGradient>
          ))}
        </defs>

        {/* horizon arc */}
        <path
          d="M -1 1 A 1 1 0 0 1 1 1"
          fill="none"
          stroke="#8a6e2f"
          strokeWidth="0.003"
        />

        <g id="chart-group">
          {/* constellation lines */}
          {constellation_lines.map((line, i) => {
            const a = hipToPos.get(line.hip_from)
            const b = hipToPos.get(line.hip_to)
            if (!a || !b) return null
            return (
              <line
                key={i}
                x1={a.x} y1={a.y}
                x2={b.x} y2={b.y}
                stroke="#c9a84c"
                strokeWidth="0.0012"
                strokeOpacity={0.25}
              />
            )
          })}

          {/* stars */}
          {stars.map(s => {
            const r = starRadius(s.magnitude)
            const gradIdx = Math.min(9, Math.round(s.magnitude * 1.5))
            return (
              <circle
                key={s.hip}
                cx={s.x}
                cy={s.y}
                r={r}
                fill={`url(#sg${gradIdx})`}
                opacity={starOpacity(s.magnitude)}
              />
            )
          })}
        </g>
      </svg>

      {/* overlay controls */}
      <div className="absolute top-3 right-3 flex gap-2">
        <button
          data-testid="reset-btn"
          className="btn-gold text-xs"
          onClick={resetView}
        >
          ↺
        </button>
      </div>
    </div>
  )
}
