import { BarChart3, FileUp, History, Info } from "lucide-react";
import { useMemo, useState } from "react";
import { AnalysisHistory } from "./components/AnalysisHistory";
import { CsvUpload } from "./components/CsvUpload";
import { PortfolioTable } from "./components/PortfolioTable";
import { StockDetail } from "./components/StockDetail";
import type { AnalysisHistoryRun, ValuationStock } from "./types";

type Page = "portfolio" | "upload" | "history";

const ANALYSIS_HISTORY_STORAGE_KEY = "stockadvisor.analysisHistory";
const MAX_HISTORY_RUNS = 20;

const pageItems: Array<{ id: Page; label: string; icon: typeof BarChart3 }> = [
  { id: "portfolio", label: "My Portfolio", icon: BarChart3 },
  { id: "upload", label: "CSV Upload", icon: FileUp },
  { id: "history", label: "Analysis History", icon: History },
];

function isValuationStockList(value: unknown): value is ValuationStock[] {
  return (
    Array.isArray(value) &&
    value.every((stock) => {
      if (!stock || typeof stock !== "object") {
        return false;
      }

      return typeof (stock as { ticker?: unknown }).ticker === "string";
    })
  );
}

function isAnalysisHistoryRun(value: unknown): value is AnalysisHistoryRun {
  if (!value || typeof value !== "object") {
    return false;
  }

  const run = value as Partial<AnalysisHistoryRun>;
  return (
    typeof run.id === "string" &&
    typeof run.createdAt === "string" &&
    isValuationStockList(run.stocks)
  );
}

function readAnalysisHistory(): AnalysisHistoryRun[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const rawHistory = window.localStorage.getItem(ANALYSIS_HISTORY_STORAGE_KEY);
    if (!rawHistory) {
      return [];
    }

    const parsedHistory: unknown = JSON.parse(rawHistory);
    if (!Array.isArray(parsedHistory)) {
      return [];
    }

    return parsedHistory.filter(isAnalysisHistoryRun).slice(0, MAX_HISTORY_RUNS);
  } catch {
    return [];
  }
}

function saveAnalysisHistory(runs: AnalysisHistoryRun[]) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(
    ANALYSIS_HISTORY_STORAGE_KEY,
    JSON.stringify(runs.slice(0, MAX_HISTORY_RUNS)),
  );
}

function createHistoryRun(stocks: ValuationStock[]): AnalysisHistoryRun {
  const id =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

  return {
    id,
    createdAt: new Date().toISOString(),
    stocks,
  };
}

function App() {
  const [activePage, setActivePage] = useState<Page>("portfolio");
  const [valuations, setValuations] = useState<ValuationStock[]>([]);
  const [selectedTicker, setSelectedTicker] = useState<string>("");
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistoryRun[]>(
    readAnalysisHistory,
  );

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
    if (stocks.length > 0) {
      const historyRun = createHistoryRun(stocks);
      setAnalysisHistory((currentHistory) => {
        const nextHistory = [historyRun, ...currentHistory].slice(
          0,
          MAX_HISTORY_RUNS,
        );
        saveAnalysisHistory(nextHistory);
        return nextHistory;
      });
    }
    setActivePage("portfolio");
  }

  function handleLoadHistoryRun(run: AnalysisHistoryRun) {
    setValuations(run.stocks);
    setSelectedTicker(run.stocks[0]?.ticker ?? "");
    setActivePage("portfolio");
  }

  function handleClearHistory() {
    saveAnalysisHistory([]);
    setAnalysisHistory([]);
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
              {activePage === "history" && "Analysis history"}
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

        {activePage === "history" && (
          <AnalysisHistory
            runs={analysisHistory}
            onLoadRun={handleLoadHistoryRun}
            onClearHistory={handleClearHistory}
          />
        )}
      </section>
    </main>
  );
}

export default App;
