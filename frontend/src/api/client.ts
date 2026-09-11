import type { DayFile, ParseResponse } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function parseReports(dayFiles: DayFile[]): Promise<ParseResponse> {
  const formData = new FormData();
  for (const { file, label } of dayFiles) {
    formData.append("files", file);
    formData.append("day_labels", label);
  }

  const res = await fetch(`${API_BASE}/parse`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Parse request failed (${res.status}): ${text}`);
  }

  return res.json();
}
