import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000",
});

export const inferECG = (ecgArray) =>
  API.post("/infer", { ecg: ecgArray });
// src/services/api.js

export async function checkHealth() {
  const res = await fetch("http://localhost:5000/api/health");
  return res.json();
}

export async function fetchDiagnosis(ecgArray, fs) {
  const res = await fetch("http://localhost:5000/api/diagnosis", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ecg: ecgArray, fs }),
  });

  if (!res.ok) {
    throw new Error("Failed to fetch diagnosis");
  }
  return res.json();
}
