import { History } from "lucide-react";

export function AnalysisHistory() {
  return (
    <section className="panel placeholder-panel">
      <div className="placeholder-icon" aria-hidden="true">
        <History size={26} />
      </div>
      <div>
        <p className="eyebrow">Longitudinal view</p>
        <h3>Analysis history</h3>
        <p>
          Future versions can store historical valuation results over time and
          compare changes in assumptions, fair value estimates, and implied
          growth.
        </p>
      </div>
      <div className="history-preview" aria-label="History placeholder rows">
        <div>
          <span>Run date</span>
          <strong>Pending</strong>
        </div>
        <div>
          <span>Portfolio snapshot</span>
          <strong>Pending</strong>
        </div>
        <div>
          <span>Assumption changes</span>
          <strong>Pending</strong>
        </div>
      </div>
    </section>
  );
}
