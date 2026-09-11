import type { ParsedDays, StationTableRow } from "./types";

export type StationBreakout = Record<string, Record<string, StationTableRow[]>>;

/**
 * Turn { day: { station: { shift: items[] } } } into
 * { station: { shift: [{name, values: {day: qty}}] } }, generalized to any
 * number of days. Station, shift, and item ordering all follow first-seen
 * order across the day list (not alphabetical), so the output reads in the
 * same order the source reports do.
 */
export function buildBreakout(parsedDays: ParsedDays, dayOrder: string[]): StationBreakout {
  const breakout: StationBreakout = {};
  // station -> shift -> item name -> row (kept alongside `breakout` for O(1) lookups while preserving insertion order)
  const rowIndex: Record<string, Record<string, Record<string, StationTableRow>>> = {};

  for (const day of dayOrder) {
    const stationReport = parsedDays[day];
    if (!stationReport) continue;

    for (const [station, shifts] of Object.entries(stationReport)) {
      breakout[station] ??= {};
      rowIndex[station] ??= {};

      for (const [shift, items] of Object.entries(shifts)) {
        breakout[station][shift] ??= [];
        rowIndex[station][shift] ??= {};

        for (const item of items) {
          let row = rowIndex[station][shift][item.name];
          if (!row) {
            row = { name: item.name, values: {} };
            rowIndex[station][shift][item.name] = row;
            breakout[station][shift].push(row);
          }
          row.values[day] = (row.values[day] ?? 0) + item.qty;
        }
      }
    }
  }

  return breakout;
}
