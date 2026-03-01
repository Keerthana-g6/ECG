import React, { useEffect, useState } from 'react';
import ECGChart from './components/ECGChart';
import StatsPanel from './components/StatsPanel';
import axios from 'axios';

// BACKEND URLs
const LIVE_ECG_URL = "http://192.168.0.10:5000/live_ecg";
const LATEST_RESULT_URL = "http://192.168.0.10:5000/latest_result";
const PROCESSED_ECG_URL = "http://192.168.0.10:5000/processed_ecg";

export default function App() {

  const [rawECG, setRawECG] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [processed, setProcessed] = useState(null);

  // ============================================================
  // 🔥 1. FETCH LIVE ECG
  // ============================================================
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const res = await fetch(LIVE_ECG_URL);
        const json = await res.json();

        if (json.ecg) {
          setRawECG(json.ecg.map((v, i) => ({ index: i, value: v })));
        }
      } catch (err) {
        console.log("ECG fetch error:", err);
      }
    }, 300);

    return () => clearInterval(id);
  }, []);

  // ============================================================
  // 🔥 2. FETCH ML ANALYSIS
  // ============================================================
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const res = await axios.get(LATEST_RESULT_URL);
        if (res.data) setAnalysis(res.data);
      } catch (e) {
        console.log("Analysis fetch error:", e);
      }
    }, 1300);

    return () => clearInterval(id);
  }, []);

  // ============================================================
  // 🔥 3. FETCH PROCESSED ECG SIGNALS
  // ============================================================
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const res = await axios.get(PROCESSED_ECG_URL);
        const d = res.data;

        if (!d) return;

        const toChart = arr => arr.map((v, i) => ({
          index: i,
          value: v
        }));

        setProcessed({
          filtered: toChart(d.filtered),
          clean: toChart(d.clean),
          baseline: toChart(d.baseline),

          r_peaks_chart: d.r_peaks.map(i => ({
            index: i,
            value: d.clean[i] || 0
          }))
        });

      } catch (err) {
        console.log("Processed ECG fetch error:", err);
      }
    }, 1000);

    return () => clearInterval(id);
  }, []);

  // ============================================================
  // UI
  // ============================================================
  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans">
      <div className="max-w-6xl mx-auto">

        {/* HEADER */}
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">ECG AI — Live Monitoring</h1>

          <div className="text-sm text-gray-600">
            Status:
            {rawECG.length > 0 ? (
              <span className="text-green-600 ml-1">Receiving ECG</span>
            ) : (
              <span className="text-red-600 ml-1">Waiting...</span>
            )}
          </div>
        </header>

        {/* GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          
          {/* LIVE ECG */}
          <div className="lg:col-span-2 bg-white p-4 rounded shadow">
            <h2 className="text-xl font-semibold mb-2">Live ECG</h2>
            <ECGChart data={rawECG} />
          </div>

          {/* STATS PANEL */}
          <div className="bg-white p-4 rounded shadow">
            <StatsPanel analysis={analysis} />
          </div>

        </div>

        {/* ADVANCED PROCESSING */}
        <div className="mt-6 bg-white p-4 rounded shadow">
          <h3 className="text-lg font-semibold mb-4">Advanced ECG Processing</h3>

          {!processed ? (
            <div className="text-gray-500">Processing...</div>
          ) : (
            <>

              {/* 3 SMALL GRAPHS */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

                <div>
                  <h4 className="text-sm font-semibold mb-1">Band-pass Filtered</h4>
                  <ECGChart data={processed.filtered} />
                </div>

                <div>
                  <h4 className="text-sm font-semibold mb-1">Baseline Removed</h4>
                  <ECGChart data={processed.clean} />
                </div>

                <div>
                  <h4 className="text-sm font-semibold mb-1">R-Peaks</h4>
                  <ECGChart
                    data={processed.clean.map((point, i) => ({
                      index: i,
                      value: processed.r_peaks_chart.some(p => p.index === i)
                        ? point.value + 300 // peak highlight
                        : point.value
                    }))}
                  />
                </div>

              </div>

              {/* BIG CLEAN ECG (FINAL SIGNAL) */}
              <div className="mt-10">
                <h3 className="text-lg font-semibold mb-2">Final Clean ECG</h3>
                <ECGChart data={processed.clean} />
              </div>

              {/* ANALYSIS */}
              <div className="mt-6 bg-gray-50 p-4 rounded shadow">
                <h3 className="text-lg font-semibold mb-3">AI Analysis</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-700">
                  <p><strong>Disease:</strong> {analysis?.disease_dl || "--"}</p>
                  <p><strong>Confidence:</strong> {analysis?.confidence_dl ? (analysis.confidence_dl * 100).toFixed(2) : "--"}%</p>
                  <p><strong>Heart Rate:</strong> {analysis?.hrv?.heart_rate || "--"} bpm</p>
                  <p><strong>Risk:</strong> {analysis?.risk?.toFixed(2) || "--"}%</p>
                </div>
              </div>

            </>
          )}
        </div>

      </div>
    </div>
  );
}
