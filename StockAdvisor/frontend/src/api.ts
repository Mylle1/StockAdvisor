import type {
  MappingResponse,
  TickerMappingPayload,
  UploadResponse,
  ValuationResponse,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001";

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>;
  }

  let message = "The backend request failed.";
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      message = payload.detail;
    }
  } catch {
    message = response.statusText || message;
  }

  throw new Error(message);
}

export async function uploadNordnetCsv(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/uploads/nordnet`, {
    method: "POST",
    body: formData,
  });

  return parseResponse<UploadResponse>(response);
}

export async function confirmTickerMappings(mappings: TickerMappingPayload[]) {
  const response = await fetch(`${API_BASE_URL}/api/ticker-mappings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ mappings }),
  });

  return parseResponse<MappingResponse>(response);
}

export async function runValuations() {
  const response = await fetch(`${API_BASE_URL}/api/valuations/run`, {
    method: "POST",
  });

  return parseResponse<ValuationResponse>(response);
}
