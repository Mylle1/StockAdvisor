import { History, RotateCcw, Trash2 } from "lucide-react";
import type { AnalysisHistoryRun } from "../types";
import { formatFairValue, formatModel, formatPercent } from "../utils/formatters";

type AnalysisHistoryProps = {
  runs: AnalysisHistoryRun[];
  onLoadRun: (run: AnalysisHistoryRun) => void;
  onClearHistory: () => void;
};

function isFiniteNumber(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function formatRunDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function getAverageUpside(run: AnalysisHistoryRun) {
  const upsideValues = run.stocks
    .map((stock) => stock.upsidePct)
    .filter(isFiniteNumber);

  if (upsideValues.length === 0) {
    return null;
  }

  return upsideValues.reduce((sum, value) => sum + value, 0) / upsideValues.length;
}

function getFairValuePreview(run: AnalysisHistoryRun) {
  const stockWithFairValue = run.stocks.find((stock) =>
    isFiniteNumber(stock.fairValue),
  );

  if (!stockWithFairValue) {
    return "-";
  }

  return `${stockWithFairValue.ticker} ${formatFairValue(
    stockWithFairValue.fairValue,
  )}`;
}

function getModelSummary(run: AnalysisHistoryRun) {
  const modelCounts = run.stocks.reduce(
    (counts, stock) => ({
      ...counts,
      [stock.modelUsed]: counts[stock.modelUsed] + 1,
    }),
    { dcf: 0, reverse_dcf: 0 },
  );

  return `${modelCounts.dcf} ${formatModel("dcf")} / ${modelCounts.reverse_dcf} ${formatModel("reverse_dcf")}`;
}

export function AnalysisHistory({
  runs,
  onLoadRun,
  onClearHistory,
}: AnalysisHistoryProps) {
  if (runs.length === 0) {
    return (
      <section className="panel history-panel">
        <div className="history-empty">
          <div className="placeholder-icon" aria-hidden="true">
            <History size={26} />
          </div>
          <div>
            <p className="eyebrow">Longitudinal view</p>
            <h3>Analysis history</h3>
            <p>
              Completed valuation runs will appear here after you run an
              analysis from the CSV upload page.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="panel history-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Longitudinal view</p>
          <h3>Analysis history</h3>
        </div>
        <span className="muted-label">{runs.length} saved runs</span>
      </div>

      <div className="history-table table-wrap">
        <table>
          <thead>
            <tr>
              <th>Run date</th>
              <th>Securities</th>
              <th>Models</th>
              <th>Avg. upside</th>
              <th>Fair value sample</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id}>
                <td>{formatRunDate(run.createdAt)}</td>
                <td>{run.stocks.length}</td>
                <td>{getModelSummary(run)}</td>
                <td>{formatPercent(getAverageUpside(run))}</td>
                <td>{getFairValuePreview(run)}</td>
                <td>
                  <button
                    className="primary-button"
                    type="button"
                    onClick={() => onLoadRun(run)}
                  >
                    <RotateCcw size={16} aria-hidden="true" />
                    <span>Open run</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="history-actions">
        <button className="primary-button" type="button" onClick={onClearHistory}>
          <Trash2 size={16} aria-hidden="true" />
          <span>Clear history</span>
        </button>
      </div>
    </section>
  );
}
