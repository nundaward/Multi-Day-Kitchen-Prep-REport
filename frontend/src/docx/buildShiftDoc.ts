import { Document, Packer, PageBreak, Paragraph, Table, TableCell, TableRow, TextRun, WidthType } from "docx";
import type { StationBreakout } from "../breakout";

/** One page per station: a heading, then one table per shift with an Item
 * column plus one column per day (generalized -- no hardcoded day count). */
export function buildShiftDoc(breakout: StationBreakout, dayOrder: string[]): Document {
  const stations = Object.keys(breakout);
  const children: (Paragraph | Table)[] = [];

  stations.forEach((station, stationIndex) => {
    if (stationIndex > 0) {
      children.push(new Paragraph({ children: [new PageBreak()] }));
    }

    children.push(
      new Paragraph({
        children: [new TextRun({ text: station, bold: true, size: 32 })],
        spacing: { after: 200 },
      })
    );

    for (const [shift, rows] of Object.entries(breakout[station])) {
      children.push(
        new Paragraph({
          children: [new TextRun({ text: shift, bold: true, size: 24 })],
          spacing: { before: 200, after: 100 },
        })
      );

      children.push(buildShiftTable(rows, dayOrder));
    }
  });

  return new Document({
    sections: [{ children }],
  });
}

function buildShiftTable(
  rows: { name: string; values: Record<string, number> }[],
  dayOrder: string[]
): Table {
  const headerRow = new TableRow({
    children: [
      headerCell("Item"),
      ...dayOrder.map((day) => headerCell(day)),
    ],
  });

  const bodyRows = rows.map(
    (row) =>
      new TableRow({
        children: [
          bodyCell(row.name),
          ...dayOrder.map((day) => bodyCell(String(row.values[day] ?? 0))),
        ],
      })
  );

  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [headerRow, ...bodyRows],
  });
}

function headerCell(text: string): TableCell {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text, bold: true })] })],
  });
}

function bodyCell(text: string): TableCell {
  return new TableCell({ children: [new Paragraph(text)] });
}

export async function downloadShiftDoc(
  breakout: StationBreakout,
  dayOrder: string[],
  filename = "kitchen-report-breakout.docx"
): Promise<void> {
  const { saveAs } = await import("file-saver");
  const doc = buildShiftDoc(breakout, dayOrder);
  const blob = await Packer.toBlob(doc);
  saveAs(blob, filename);
}
