// src/components/ECGBaselineChart.jsx

import React from "react";

const ECGBaselineChart = ({ ecg, baseline }) => {
  // Very simple SVG-based visualization for demo
  if (!ecg || ecg.length === 0) return null;

  const width = 400;
  const height = 150;

  const maxVal = Math.max(...ecg, ...(baseline || [0]));
  const minVal = Math.min(...ecg, ...(baseline || [0]));
  const range = maxVal - minVal || 1;

  const toY = (v) => height - ((v - minVal) / range) * height;

  const pathFromArray = (arr) =>
    arr
      .map((v, i) => {
        const x = (i / (arr.length - 1 || 1)) * width;
        const y = toY(v);
        return `${i === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");

  const ecgPath = pathFromArray(ecg);
  const baselinePath = baseline && baseline.length ? pathFromArray(baseline) : "";

  return (
    <div className="card">
      <h3>ECG & Baseline Drift</h3>
      <svg width={width} height={height} style={{ border: "1px solid #ccc" }}>
        <path d={ecgPath} fill="none" strokeWidth="1" />
        {baselinePath && (
          <path
            d={baselinePath}
            fill="none"
            strokeWidth="1"
            strokeDasharray="4 2"
          />
        )}
      </svg>
      <p style={{ fontSize: "0.8rem", marginTop: "0.5rem" }}>
        Solid line: cleaned ECG, dashed line: baseline drift
      </p>
    </div>
  );
};

export default ECGBaselineChart;
