import { ChevronDown } from "lucide-react";
import type { ValuationStock } from "../types";
import {
  formatFairValue,
  formatLargeNumber,
  formatModel,
  formatNumber,
  formatPercent,
} from "../utils/formatters";

type StockDetailProps = {
  stock: ValuationStock;
};

export function StockDetail({ stock }: StockDetailProps) {
  const assumptionRows =
    stock.modelUsed === "dcf"
      ? [
          ["Current price", `${stock.currency} ${formatNumber(stock.currentPrice)}`],
          ["Revenue last year", formatLargeNumber(stock.assumptions.revenueLastYear)],
          ["Revenue growth", formatPercent(stock.assumptions.revenueGrowth ?? null)],
          ["Target FCF margin", formatPercent(stock.assumptions.targetFcfMargin ?? null)],
          ["WACC", formatPercent(stock.assumptions.wacc)],
          ["Terminal growth", formatPercent(stock.assumptions.terminalGrowth)],
          ["Forecast years", String(stock.assumptions.forecastYears)],
          ["Net debt", formatLargeNumber(stock.assumptions.netDebt ?? null)],
          [
            "Shares outstanding",
            formatLargeNumber(stock.assumptions.sharesOutstanding ?? null),
          ],
        ]
      : [
          ["Current price", `${stock.currency} ${formatNumber(stock.currentPrice)}`],
          ["Revenue last year", formatLargeNumber(stock.assumptions.revenueLastYear)],
          [
            "Normalized target FCF margin",
            formatPercent(stock.assumptions.normalizedTargetFcfMargin ?? null),
          ],
          ["WACC", formatPercent(stock.assumptions.wacc)],
          ["Terminal growth", formatPercent(stock.assumptions.terminalGrowth)],
          ["Forecast years", String(stock.assumptions.forecastYears)],
          [
            "Implied revenue growth",
            formatPercent(stock.assumptions.impliedRevenueGrowth ?? null),
          ],
        ];

  return (
    <aside className="panel detail-panel" aria-label="Stock detail view">
      <div className="detail-header">
        <div>
          <p className="eyebrow">Selected security</p>
          <h3>{stock.ticker}</h3>
          <p className="company-name">{stock.companyName}</p>
        </div>
        <span className={`model-chip ${stock.modelUsed}`}>
          {formatModel(stock.modelUsed)}
        </span>
      </div>

      <div className="metric-grid">
        <Metric label="Current price" value={`${stock.currency} ${formatNumber(stock.currentPrice)}`} />
        <Metric label="Fair value" value={formatFairValue(stock.fairValue)} />
        <Metric label="Upside" value={formatPercent(stock.upsidePct)} />
        <Metric label="Implied growth" value={formatPercent(stock.impliedGrowth)} />
      </div>

      <details className="assumptions-card" open>
        <summary>
          <span>Show parameters</span>
          <ChevronDown size={18} aria-hidden="true" />
        </summary>
        <dl className="parameter-list">
          {assumptionRows.map(([label, value]) => (
            <div key={label} className="parameter-row">
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </details>

      <div className="method-note">
        This view presents valuation output and model assumptions for transparency.
        It is intended as decision support, not as investment advice.
      </div>
    </aside>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
