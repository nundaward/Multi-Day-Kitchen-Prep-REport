import type { ParsedDays, StationTableRow } from "./types";

export type StationBreakout = Record<string, Record<string, StationTableRow[]>>;

const SHIFT_NUMBER = /^Shift (\d+)$/;

/** "Shift 1" < "Shift 2" < ... < anything else (e.g. "Unassigned"), which
 * sorts last, alphabetically among itself. */
function shiftSortKey(label: string): [number, string] {
  const m = SHIFT_NUMBER.exec(label);
  return m ? [Number(m[1]), ""] : [Number.POSITIVE_INFINITY, label];
}

function sortShiftLabels(shifts: Record<string, StationTableRow[]>): Record<string, StationTableRow[]> {
  const sortedLabels = Object.keys(shifts).sort((a, b) => {
    const [aNum, aLabel] = shiftSortKey(a);
    const [bNum, bLabel] = shiftSortKey(b);
    return aNum !== bNum ? aNum - bNum : aLabel.localeCompare(bLabel);
  });

  const sorted: Record<string, StationTableRow[]> = {};
  for (const label of sortedLabels) sorted[label] = shifts[label];
  return sorted;
}

/**
 * Turn { day: { station: { shift: items[] } } } into
 * { station: { shift: [{name, values: {day: qty}}] } }, generalized to any
 * number of days. Station and item ordering follow first-seen order across
 * the day list (not alphabetical); shifts within a station are sorted
 * numerically (Shift 1, Shift 2, ...) regardless of first-seen order.
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

  for (const station of Object.keys(breakout)) {
    breakout[station] = sortShiftLabels(breakout[station]);
  }

  return breakout;
}
