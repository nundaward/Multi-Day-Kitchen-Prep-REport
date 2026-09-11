import type { StationBreakout } from "../breakout";
import { REPORT_TITLE, buildSourceNote } from "../reportMeta";

interface Props {
  breakout: StationBreakout;
  dayOrder: string[];
}

export function ParsePreview({ breakout, dayOrder }: Props) {
  const stations = Object.keys(breakout);

  if (stations.length === 0) {
    return <p>No stations parsed yet.</p>;
  }

  return (
    <div className="parse-preview">
      <div className="print-header">
        <h1>{REPORT_TITLE}</h1>
        <h2>Item Needs, {dayOrder.join(" vs. ")}</h2>
        <p className="print-source-note">{buildSourceNote(dayOrder)}</p>
      </div>

      {stations.map((station) => (
        <section key={station} className="parse-preview__station">
          <h2>{station}</h2>
          {Object.entries(breakout[station]).map(([shift, rows]) => (
            <div key={shift} className="parse-preview__shift">
              <h3>{shift}</h3>
              <table>
                <thead>
                  <tr>
                    <th>Item</th>
                    {dayOrder.map((day) => (
                      <th key={day}>{day}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.name}>
                      <td>{row.name}</td>
                      {dayOrder.map((day) => (
                        <td key={day}>{row.values[day] ?? "—"}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}
