import axios from "axios";

const GENERIC_FIELD_LABELS = new Set(["detail", "non_field_errors"]);

function fromResponseData(data: unknown): string | null {
  if (typeof data === "string" && data.trim().length > 0) return data;

  if (!data || typeof data !== "object" || Array.isArray(data)) return null;

  const messages: string[] = [];

  for (const [field, value] of Object.entries(data as Record<string, unknown>)) {
    const list = Array.isArray(value) ? value : [value];
    const texts = list.filter(
      (item): item is string =>
        typeof item === "string" && item.trim().length > 0
    );

    if (texts.length === 0) continue;

    messages.push(
      GENERIC_FIELD_LABELS.has(field)
        ? texts.join(" ")
        : texts.map((text) => `${field}: ${text}`).join(" ")
    );
  }

  return messages.length ? messages.join(" ") : null;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const fromBody = fromResponseData(error.response?.data);
    if (fromBody) return fromBody;

    if (!error.response) {
      return "Não foi possível conectar ao servidor. Verifique sua conexão.";
    }
  }

  return fallback;
}
