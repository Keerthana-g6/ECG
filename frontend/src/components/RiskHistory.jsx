import React from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'


export default function RiskHistory({ history }){
// history: [{time, risk}, ...]
return (
<LineChart width={800} height={250} data={history}>
<CartesianGrid strokeDasharray="3 3" />
<XAxis dataKey="time" />
<YAxis domain={[0,100]} />
<Tooltip />
<Line type="monotone" dataKey="risk" stroke="#ef4444" dot={false} />
</LineChart>
)
}