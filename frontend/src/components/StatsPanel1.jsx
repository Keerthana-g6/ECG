import React from 'react'


export default function StatsPanel({analysis}){
if(!analysis) return <div className="stats">Waiting for data...</div>
return (
<div className="stats">
<h2>Analysis</h2>
<p><strong>Condition:</strong> {analysis.label}</p>
<p><strong>Risk:</strong> {analysis.risk}%</p>
<p><strong>HR:</strong> {analysis.hrv ? analysis.hrv.heart_rate : 'N/A'}</p>
<p><strong>SDNN:</strong> {analysis.hrv ? analysis.hrv.sdnn : 'N/A'}</p>
<p><strong>RMSSD:</strong> {analysis.hrv ? analysis.hrv.rmssd : 'N/A'}</p>
</div>
)
}