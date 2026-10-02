import { useEffect, useState } from "react";
import { getApiErrorMessage } from "@/utils/apiError";

export function useFetch<T>(fetchFunction: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setError(null);
      setLoading(true);

      try {
        const result = await fetchFunction();
        if (active) setData(result);
      } catch (e) {
        if (active) setError(getApiErrorMessage(e, "Erro ao carregar dados"));
      } finally {
        if (active) setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [fetchFunction]);

  return { data, loading, error };
}
