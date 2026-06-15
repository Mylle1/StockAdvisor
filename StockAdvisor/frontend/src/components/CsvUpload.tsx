import { FileUp, Play, Save } from "lucide-react";
import { useMemo, useState } from "react";
import {
  confirmTickerMappings,
  runValuations,
  uploadNordnetCsv,
} from "../api";
import type { Holding, ValuationError, ValuationStock } from "../types";
import { formatNumber } from "../utils/formatters";

type CsvUploadProps = {
  onValuationsReady: (stocks: ValuationStock[]) => void;
};

type LoadState = "idle" | "uploading" | "saving" | "valuating";

export function CsvUpload({ onValuationsReady }: CsvUploadProps) {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [selectedFileName, setSelectedFileName] = useState("");
  const [status, setStatus] = useState("Upload a Nordnet CSV report to begin.");
  const [errors, setErrors] = useState<ValuationError[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [filteredOutCount, setFilteredOutCount] = useState(0);

  const allMapped = useMemo(
    () => holdings.length > 0 && holdings.every((holding) => holding.ticker?.trim()),
    [holdings],
  );

  async function handleUpload(file: File | null) {
    if (!file) {
      return;
    }

    setSelectedFileName(file.name);
    setErrors([]);
    setLoadState("uploading");
    setStatus("Importing holdings from the report...");

    try {
      const response = await uploadNordnetCsv(file);
      setHoldings(response.holdings);
      setFilteredOutCount(response.filteredOutCount);
      setStatus(
        `${response.holdings.length} stock holdings imported. Enter or review tickers before valuation.`,
      );
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Upload failed.");
      setHoldings([]);
    } finally {
      setLoadState("idle");
    }
  }

  function updateTicker(index: number, ticker: string) {
    setHoldings((currentHoldings) =>
      currentHoldings.map((holding, holdingIndex) =>
        holdingIndex === index ? { ...holding, ticker } : holding,
      ),
    );
  }

  async function handleRunValuation() {
    setErrors([]);
    setLoadState("saving");
    setStatus("Saving ticker mappings...");

    try {
      const mappingResponse = await confirmTickerMappings(
        holdings.map((holding) => ({
          name: holding.name,
          ticker: holding.ticker ?? "",
        })),
      );
      setHoldings(mappingResponse.holdings);

      if (mappingResponse.unmappedNames.length > 0) {
        setStatus("Add tickers for all holdings before running valuation.");
        return;
      }

      setLoadState("valuating");
      setStatus("Running valuation models...");
      const valuationResponse = await runValuations();
      setErrors(valuationResponse.errors);
      onValuationsReady(valuationResponse.results);
      const reviewMessage =
        valuationResponse.errors.length > 0
          ? ` ${valuationResponse.errors.length} holdings need review.`
          : "";
      setStatus(
        valuationResponse.results.length > 0
          ? `${valuationResponse.results.length} valuations completed.${reviewMessage}`
          : "No valuations completed. Review the messages below.",
      );
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Valuation failed.");
    } finally {
      setLoadState("idle");
    }
  }

  async function handleSaveMappings() {
    setErrors([]);
    setLoadState("saving");
    setStatus("Saving ticker mappings...");

    try {
      const mappingResponse = await confirmTickerMappings(
        holdings.map((holding) => ({
          name: holding.name,
          ticker: holding.ticker ?? "",
        })),
      );
      setHoldings(mappingResponse.holdings);
      setStatus("Ticker mappings saved.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Saving mappings failed.");
    } finally {
      setLoadState("idle");
    }
  }

  return (
    <section className="panel upload-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Data import</p>
          <h3>Nordnet CSV upload</h3>
        </div>
        <span className="muted-label">{holdings.length} stock holdings</span>
      </div>

      <label className="upload-zone active-upload">
        <input
          type="file"
          accept=".csv,.tsv,text/csv,text/tab-separated-values"
          onChange={(event) => void handleUpload(event.target.files?.[0] ?? null)}
          disabled={loadState !== "idle"}
        />
        <FileUp size={20} aria-hidden="true" />
        <span>{selectedFileName || "Choose Nordnet report"}</span>
        <small>{status}</small>
      </label>

      {filteredOutCount > 0 && (
        <p className="inline-note">
          {filteredOutCount} non-stock or incomplete rows were excluded from this run.
        </p>
      )}

      {holdings.length > 0 && (
        <>
          <div className="table-wrap mapping-table">
            <table>
              <thead>
                <tr>
                  <th>Holding</th>
                  <th>Currency</th>
                  <th>Quantity</th>
                  <th>Current price</th>
                  <th>yfinance ticker</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((holding, index) => (
                  <tr key={`${holding.name}-${index}`}>
                    <td>{holding.name}</td>
                    <td>{holding.currency}</td>
                    <td>{formatNumber(holding.quantity)}</td>
                    <td>{formatNumber(holding.current_price)}</td>
                    <td>
                      <input
                        className="ticker-input"
                        value={holding.ticker ?? ""}
                        onChange={(event) => updateTicker(index, event.target.value)}
                        placeholder="e.g. NOVO-B.CO"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="upload-actions">
            <button
              className="primary-button"
              type="button"
              onClick={() => void handleSaveMappings()}
              disabled={loadState !== "idle" || !allMapped}
            >
              <Save size={17} aria-hidden="true" />
              <span>Save mappings</span>
            </button>
            <button
              className="primary-button emphasized"
              type="button"
              onClick={() => void handleRunValuation()}
              disabled={loadState !== "idle" || !allMapped}
            >
              <Play size={17} aria-hidden="true" />
              <span>Run valuation</span>
            </button>
          </div>
        </>
      )}

      {errors.length > 0 && (
        <div className="run-messages" role="status">
          <strong>Review needed</strong>
          {errors.map((error) => (
            <p key={`${error.name}-${error.ticker ?? "missing"}`}>
              {error.ticker ? `${error.ticker} - ` : ""}
              {error.name}: {error.message}
            </p>
          ))}
        </div>
      )}
    </section>
  );
}
