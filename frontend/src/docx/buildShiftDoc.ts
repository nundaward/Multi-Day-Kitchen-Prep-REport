import {
  BorderStyle,
  Document,
  Header,
  PageBreak,
  Packer,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} from "docx";
import type { StationBreakout } from "../breakout";
import { REPORT_TITLE, buildSourceNote } from "../reportMeta";

const HEADER_ACCENT = "1F4E78";
const HEADER_FILL = "D9E2F3";
const BODY_ALT_FILL = "F2F2F2";
const BORDER_COLOR = "999999";

const CELL_BORDER = {
  top: { style: BorderStyle.SINGLE, size: 2, color: BORDER_COLOR },
  bottom: { style: BorderStyle.SINGLE, size: 2, color: BORDER_COLOR },
  left: { style: BorderStyle.SINGLE, size: 2, color: BORDER_COLOR },
  right: { style: BorderStyle.SINGLE, size: 2, color: BORDER_COLOR },
};

/** One page per station, with a running page header (report title + date
 * range) and a header row per shift table -- mirrors the reference
 * "Item Needs, Monday vs. Tuesday" printout: title block once up top, then
 * each station's shift tables, one station per page. */
export function buildShiftDoc(breakout: StationBreakout, dayOrder: string[]): Document {
  const stations = Object.keys(breakout);
  const dateRange = dayOrder.join(" vs. ");
  const children: (Paragraph | Table)[] = [];

  children.push(
    new Paragraph({
      children: [new TextRun({ text: REPORT_TITLE, bold: true, size: 32, color: HEADER_ACCENT })],
      spacing: { after: 100 },
    }),
    new Paragraph({
      children: [new TextRun({ text: `Item Needs, ${dateRange}`, bold: true, size: 26, color: HEADER_ACCENT })],
      spacing: { after: 200 },
    }),
    new Paragraph({
      children: [
        new TextRun({
          italics: true,
          size: 18,
          text: buildSourceNote(dayOrder),
        }),
      ],
      spacing: { after: 300 },
    })
  );

  stations.forEach((station, stationIndex) => {
    if (stationIndex > 0) {
      children.push(new Paragraph({ children: [new PageBreak()] }));
    }

    children.push(
      new Paragraph({
        children: [new TextRun({ text: station, bold: true, size: 28, color: HEADER_ACCENT })],
        spacing: { after: 150 },
      })
    );

    for (const [shift, rows] of Object.entries(breakout[station])) {
      children.push(
        new Paragraph({
          children: [new TextRun({ text: shift, bold: true, size: 22 })],
          spacing: { before: 200, after: 100 },
        })
      );

      children.push(buildShiftTable(rows, dayOrder));
    }
  });

  return new Document({
    sections: [
      {
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: HEADER_ACCENT } },
                children: [
                  new TextRun({
                    text: `${REPORT_TITLE} | Item Needs, ${dateRange}`,
                    bold: true,
                    size: 18,
                  }),
                ],
              }),
            ],
          }),
        },
        children,
      },
    ],
  });
}

function buildShiftTable(
  rows: { name: string; values: Record<string, number> }[],
  dayOrder: string[]
): Table {
  const headerRow = new TableRow({
    tableHeader: true,
    children: [headerCell("Item"), ...dayOrder.map((day) => headerCell(day))],
  });

  const bodyRows = rows.map(
    (row, i) =>
      new TableRow({
        children: [
          bodyCell(row.name, i),
          ...dayOrder.map((day) => bodyCell(formatQty(row.values[day]), i)),
        ],
      })
  );

  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [headerRow, ...bodyRows],
  });
}

function formatQty(qty: number | undefined): string {
  return qty === undefined ? "—" : String(qty);
}

function headerCell(text: string): TableCell {
  return new TableCell({
    borders: CELL_BORDER,
    shading: { type: ShadingType.CLEAR, color: "auto", fill: HEADER_FILL },
    children: [new Paragraph({ children: [new TextRun({ text, bold: true })] })],
  });
}

function bodyCell(text: string, rowIndex: number): TableCell {
  return new TableCell({
    borders: CELL_BORDER,
    shading:
      rowIndex % 2 === 1 ? { type: ShadingType.CLEAR, color: "auto", fill: BODY_ALT_FILL } : undefined,
    children: [new Paragraph(text)],
  });
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
