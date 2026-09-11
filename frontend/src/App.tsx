import { useState } from "react";
import "./App.css";
import { parseReports } from "./api/client";
import { buildBreakout, type StationBreakout } from "./breakout";
import { ExportButton } from "./components/ExportButton";
import { FileUploader } from "./components/FileUploader";
import { ParsePreview } from "./components/ParsePreview";
import type { DayFile } from "./types";

function App() {
  const [dayFiles, setDayFiles] = useState<DayFile[]>([]);
  const [breakout, setBreakout] = useState<StationBreakout | null>(null);
  const [dayOrder, setDayOrder] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canParse = dayFiles.length > 0 && dayFiles.every((df) => df.label.trim() !== "");

  async function handleParse() {
    setLoading(true);
    setError(null);
    try {
      const response = await parseReports(dayFiles);
      const labels = dayFiles.map((df) => df.label);
      setDayOrder(labels);
      setBreakout(buildBreakout(response.days, labels));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <div className="no-print">
        <h1>Multi-Day Kitchen Report</h1>

        <FileUploader dayFiles={dayFiles} onChange={setDayFiles} />

        <button type="button" onClick={handleParse} disabled={!canParse || loading}>
          {loading ? "Parsing..." : "Parse reports"}
        </button>

        {error && <p className="app__error">{error}</p>}

        {breakout && (
          <>
            <ExportButton breakout={breakout} dayOrder={dayOrder} />
            <button type="button" onClick={() => window.print()}>
              Print / Save as PDF
            </button>
          </>
        )}
      </div>

      {breakout && <ParsePreview breakout={breakout} dayOrder={dayOrder} />}
    </div>
  );
}

export default App;
