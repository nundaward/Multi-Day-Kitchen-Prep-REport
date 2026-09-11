import { useState } from "react";
import type { StationBreakout } from "../breakout";
import { downloadShiftDoc } from "../docx/buildShiftDoc";

interface Props {
  breakout: StationBreakout;
  dayOrder: string[];
}

export function ExportButton({ breakout, dayOrder }: Props) {
  const [exporting, setExporting] = useState(false);

  async function handleExport() {
    setExporting(true);
    try {
      await downloadShiftDoc(breakout, dayOrder);
    } finally {
      setExporting(false);
    }
  }

  return (
    <button type="button" onClick={handleExport} disabled={exporting}>
      {exporting ? "Generating..." : "Export .docx"}
    </button>
  );
}
