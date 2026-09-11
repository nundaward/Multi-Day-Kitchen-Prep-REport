export interface ReportItem {
  name: string;
  qty: number;
}

// station -> shift label -> items
export type StationReport = Record<string, Record<string, ReportItem[]>>;

// day label -> station report
export type ParsedDays = Record<string, StationReport>;

// day label -> item name -> qty (BREAD SUMMARY-style cross-check totals, if any)
export type BreadSummaryByDay = Record<string, Record<string, number>>;

export interface ParseResponse {
  days: ParsedDays;
  bread_summary: BreadSummaryByDay;
}

export interface DayFile {
  file: File;
  label: string;
}

// One row of the breakout table for a single station: item name + qty per day.
export interface StationTableRow {
  name: string;
  values: Record<string, number>; // keyed by day label
}
