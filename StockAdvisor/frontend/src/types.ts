export type ModelUsed = "dcf" | "reverse_dcf";

export type ValuationStock = {
  ticker: string;
  companyName: string;
  modelUsed: ModelUsed;
  currency: string;
  currentPrice: number;
  fairValue: number | null;
  upsidePct: number | null;
  impliedGrowth: number | null;
  assumptions: {
    revenueLastYear: number;
    revenueGrowth?: number;
    targetFcfMargin?: number;
    normalizedTargetFcfMargin?: number;
    wacc: number;
    terminalGrowth: number;
    forecastYears: number;
    netDebt?: number;
    sharesOutstanding?: number;
    impliedRevenueGrowth?: number;
  };
  holding?: Holding;
};

export type AnalysisHistoryRun = {
  id: string;
  createdAt: string;
  stocks: ValuationStock[];
};

export type Holding = {
  platform: string;
  name: string;
  currency: string;
  quantity: number | null;
  avg_price: number | null;
  current_price: number | null;
  market_value: number | null;
  market_value_dkk: number | null;
  gain_pct: number | null;
  gain_dkk: number | null;
  ticker: string | null;
};

export type UploadResponse = {
  holdings: Holding[];
  unmappedNames: string[];
  importedCount: number;
  filteredOutCount: number;
};

export type MappingResponse = {
  holdings: Holding[];
  unmappedNames: string[];
  mappingPath: string;
};

export type TickerMappingPayload = {
  name: string;
  ticker: string;
};

export type ValuationError = {
  name: string;
  ticker?: string;
  message: string;
};

export type ValuationResponse = {
  results: ValuationStock[];
  errors: ValuationError[];
  parameters: {
    dcf: Record<string, number>;
    reverseDcf: Record<string, number>;
  };
};
