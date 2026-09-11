export const REPORT_TITLE = "Arlington Hts — Kitchen Report";

export function buildSourceNote(dayOrder: string[]): string {
  return (
    `Source: kitchen reports for ${dayOrder.join(", ")}. Quantities are each item's All Day total ` +
    "as listed on the original report for the shift shown; sub-order/prep breakdown lines have been " +
    "omitted. For Sandwich Station, quantities are each item's total across all of that shift's " +
    "orders, summed from the order-level detail since the source report doesn't give a single bold " +
    "total per item per shift the way the other stations do. A dash (—) means that item was not " +
    "needed on that day for that shift."
  );
}
