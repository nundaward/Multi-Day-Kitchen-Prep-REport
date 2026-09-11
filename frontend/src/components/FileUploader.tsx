import type { ChangeEvent } from "react";
import type { DayFile } from "../types";

interface Props {
  dayFiles: DayFile[];
  onChange: (dayFiles: DayFile[]) => void;
}

export function FileUploader({ dayFiles, onChange }: Props) {
  function handleFilesSelected(e: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(e.target.files ?? []);
    if (selected.length === 0) return;

    const newDayFiles = selected.map((file) => ({ file, label: "" }));
    onChange([...dayFiles, ...newDayFiles]);
    e.target.value = "";
  }

  function updateLabel(index: number, label: string) {
    const next = dayFiles.slice();
    next[index] = { ...next[index], label };
    onChange(next);
  }

  function removeFile(index: number) {
    onChange(dayFiles.filter((_, i) => i !== index));
  }

  return (
    <div className="file-uploader">
      <label className="file-uploader__input-label">
        Add kitchen report PDF(s)
        <input type="file" accept="application/pdf" multiple onChange={handleFilesSelected} />
      </label>

      {dayFiles.length > 0 && (
        <table className="file-uploader__table">
          <thead>
            <tr>
              <th>File</th>
              <th>Day label</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {dayFiles.map((df, i) => (
              <tr key={`${df.file.name}-${i}`}>
                <td>{df.file.name}</td>
                <td>
                  <input
                    type="text"
                    placeholder="e.g. Monday, 9/15"
                    value={df.label}
                    onChange={(e) => updateLabel(i, e.target.value)}
                  />
                </td>
                <td>
                  <button type="button" onClick={() => removeFile(i)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
