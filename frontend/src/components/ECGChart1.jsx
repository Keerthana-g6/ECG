import React from 'react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, LineElement, CategoryScale, LinearScale, PointElement } from 'chart.js'
ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement)


export default function ECGChart({data}){
const chartData = {
labels: data.map((_,i)=>i),
datasets: [{
label: 'ECG',
data: data,
fill: false,
tension: 0.1
}]
}
const options = {
animation: false,
scales: { x: { display: false }, y: { min: Math.min(...(data.slice(-200)||[0]))-0.5, max: Math.max(...(data.slice(-200)||[0]))+0.5 } }
}
return (
<div className="chart">
<Line data={chartData} options={options} />
</div>
)
}