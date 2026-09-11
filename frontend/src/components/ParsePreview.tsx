import type { StationBreakout } from "../breakout";

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
                        <td key={day}>{row.values[day] ?? 0}</td>
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
