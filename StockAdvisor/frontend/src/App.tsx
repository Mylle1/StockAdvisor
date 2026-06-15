import { BarChart3, FileUp, History, Info } from "lucide-react";
import { useMemo, useState } from "react";
import { AnalysisHistory } from "./components/AnalysisHistory";
import { CsvUpload } from "./components/CsvUpload";
import { PortfolioTable } from "./components/PortfolioTable";
import { StockDetail } from "./components/StockDetail";
import type { ValuationStock } from "./types";

type Page = "portfolio" | "upload" | "history";

const pageItems: Array<{ id: Page; label: string; icon: typeof BarChart3 }> = [
  { id: "portfolio", label: "My Portfolio", icon: BarChart3 },
  { id: "upload", label: "CSV Upload", icon: FileUp },
  { id: "history", label: "Analysis History", icon: History },
];

function App() {
  const [activePage, setActivePage] = useState<Page>("portfolio");
  const [valuations, setValuations] = useState<ValuationStock[]>([]);
  const [selectedTicker, setSelectedTicker] = useState<string>("");

  const selectedStock = useMemo<ValuationStock | null>(
    () =>
      valuations.find((stock) => stock.ticker === selectedTicker) ??
      valuations[0] ??
      null,
    [selectedTicker, valuations],
  );

  function handleValuationsReady(stocks: ValuationStock[]) {
    setValuations(stocks);
    setSelectedTicker(stocks[0]?.ticker ?? "");
    setActivePage("portfolio");
  }

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Main navigation">
        <div className="brand-block">
          <div className="brand-mark">SA</div>
          <div>
            <p className="eyebrow">StockAdvisor</p>
            <h1>Valuation workspace</h1>
          </div>
        </div>

        <nav className="nav-list">
          {pageItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={activePage === item.id ? "nav-item active" : "nav-item"}
                onClick={() => setActivePage(item.id)}
                type="button"
                title={item.label}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <section className="workspace">
        <header className="page-header">
          <div>
            <p className="eyebrow">Decision support prototype</p>
            <h2>
              {activePage === "portfolio" && "Portfolio valuation output"}
              {activePage === "upload" && "Nordnet CSV intake"}
              {activePage === "history" && "Historical analysis placeholder"}
            </h2>
          </div>
          <div className="notice" role="note">
            <Info size={16} aria-hidden="true" />
            <span>No buy/sell recommendations are produced.</span>
          </div>
        </header>

        {activePage === "portfolio" && (
          valuations.length > 0 && selectedStock ? (
            <div className="portfolio-layout">
              <section className="panel table-panel" aria-label="Portfolio table">
                <PortfolioTable
                  stocks={valuations}
                  selectedTicker={selectedStock.ticker}
                  onSelectStock={setSelectedTicker}
                />
              </section>
              <StockDetail stock={selectedStock} />
            </div>
          ) : (
            <section className="panel empty-panel">
              <p className="eyebrow">Current run</p>
              <h3>No valuation run loaded</h3>
              <p>
                Upload a Nordnet CSV, confirm tickers, and run the valuation to
                populate this workspace.
              </p>
              <button
                className="primary-button emphasized"
                type="button"
                onClick={() => setActivePage("upload")}
              >
                <FileUp size={17} aria-hidden="true" />
                <span>Upload CSV</span>
              </button>
            </section>
          )
        )}

        {activePage === "upload" && (
          <CsvUpload onValuationsReady={handleValuationsReady} />
        )}

        {activePage === "history" && <AnalysisHistory />}
      </section>
    </main>
  );
}

export default App;
