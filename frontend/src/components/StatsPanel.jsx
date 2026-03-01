import React from 'react';

export default function StatsPanel({ analysis }) {

  if (!analysis) {
    return (
      <div className="p-2 text-center text-gray-500">Waiting for data...</div>
    );
  }

  // -----------------------------
  // Map backend keys → frontend keys
  // -----------------------------
  const label = analysis.disease_dl || analysis.rf_class_label || "Unknown";

  const confidence = analysis.confidence_dl
    ? (analysis.confidence_dl * 100).toFixed(2)
    : "--";

  const probs = Array.isArray(analysis.rf_probabilities)
    ? analysis.rf_probabilities
    : [];

  const hrv = typeof analysis.hrv === "number"
    ? analysis.hrv.toFixed(2)
    : "--";

  const risk = typeof analysis.risk === "number"
    ? analysis.risk.toFixed(1)
    : "--";

  const getRiskColor = (r) => {
    if (r === '--') return "bg-gray-200 text-gray-700";
    if (r < 30) return "bg-green-100 text-green-800";
    if (r < 70) return "bg-yellow-100 text-yellow-800";
    return "bg-red-100 text-red-800";
  };

  return (
    <div>

      {/* Detection Panel */}
      <div className={`p-3 rounded ${getRiskColor(risk)}`}>
        <div className="text-sm">Detection</div>
        <div className="text-2xl font-bold">{label}</div>
        <div className="text-sm mt-1">
          Confidence: <strong>{confidence}%</strong>
        </div>
      </div>

      {/* HRV */}
      <div className="mt-4">
        <h4 className="text-sm font-medium">HRV / Heart Rate</h4>
        <div className="text-lg">{hrv}</div>
      </div>

      {/* Risk */}
      <div className="mt-4">
        <h4 className="text-sm font-medium">Risk</h4>
        <div className="text-lg">{risk}%</div>
      </div>

      {/* Probabilities (RF model) */}
      {probs.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium">RF Model – Probabilities</h4>
          <ul className="text-sm list-disc list-inside">
            {probs.map((p, i) => (
              <li key={i}>{p.toFixed(3)}</li>
            ))}
          </ul>
        </div>
      )}

    </div>
  );
}
