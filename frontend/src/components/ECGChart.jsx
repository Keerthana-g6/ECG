import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'

export default function ECGChart({ data }) {

  // downsample for performance
  const maxPoints = 1200
  const step = Math.max(1, Math.floor(data.length / maxPoints))
  const sampled = data
    .filter((_, i) => i % step === 0)
    .map((d, i) => ({ x: i, value: d.value }))

  return (
    <div style={{ width: "100%", height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={sampled}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="x" hide />

          <YAxis domain={['auto', 'auto']} width={60} />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="value"
            stroke="#1f2937"
            dot={false}
            strokeWidth={1}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
