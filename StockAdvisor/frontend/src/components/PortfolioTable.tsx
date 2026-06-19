import type { ValuationStock } from "../types";
import {
  formatFairValue,
  formatModel,
  formatNumber,
  formatPercent,
} from "../utils/formatters";

type PortfolioTableProps = {
  stocks: ValuationStock[];
  selectedTicker: string;
  onSelectStock: (ticker: string) => void;
};

export function PortfolioTable({
  stocks,
  selectedTicker,
  onSelectStock,
}: PortfolioTableProps) {
  return (
    <div>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Current run</p>
          <h3>My Portfolio</h3>
        </div>
        <span className="muted-label">{stocks.length} securities</span>
      </div>

      <div className="table-wrap">
        <table className="portfolio-table">
          <thead>
            <tr>
              <th>Company name</th>
              <th>Model used</th>
              <th>Currency</th>
              <th>Current price</th>
              <th>Fair value</th>
              <th>Upside %</th>
              <th>Implied growth</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock) => (
              <tr
                key={stock.ticker}
                className={stock.ticker === selectedTicker ? "selected-row" : ""}
                onClick={() => onSelectStock(stock.ticker)}
              >
                <td>
                  <button
                    className="link-button company-button"
                    type="button"
                    title={`${stock.companyName} (${stock.ticker})`}
                    onClick={() => onSelectStock(stock.ticker)}
                  >
                    {stock.companyName}
                  </button>
                </td>
                <td>
                  <span className={`model-chip ${stock.modelUsed}`}>
                    {formatModel(stock.modelUsed)}
                  </span>
                </td>
                <td>{stock.currency}</td>
                <td>{formatNumber(stock.currentPrice)}</td>
                <td>{formatFairValue(stock.fairValue)}</td>
                <td className={stock.upsidePct && stock.upsidePct < 0 ? "negative" : ""}>
                  {formatPercent(stock.upsidePct)}
                </td>
                <td>{formatPercent(stock.impliedGrowth)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
