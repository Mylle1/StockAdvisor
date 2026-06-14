import { FileUp } from "lucide-react";

export function CsvUpload() {
  return (
    <section className="panel placeholder-panel">
      <div className="placeholder-icon" aria-hidden="true">
        <FileUp size={26} />
      </div>
      <div>
        <p className="eyebrow">Data import</p>
        <h3>Nordnet CSV upload</h3>
        <p>
          CSV processing will be connected to the Python backend later.
        </p>
      </div>
      <label className="upload-zone">
        <input type="file" accept=".csv,text/csv" disabled />
        <span>Upload placeholder</span>
        <small>Backend integration pending</small>
      </label>
    </section>
  );
}
