export type ModelUsed = "dcf" | "reverse_dcf";

export type ValuationStock = {
  ticker: string;
  companyName: string;
  modelUsed: ModelUsed;
  currency: "USD" | "DKK";
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
};
