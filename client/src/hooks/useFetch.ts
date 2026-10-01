import { useEffect, useState } from "react";

export function useFetch<T>(fetchFunction: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const result = await fetchFunction();
        setData(result);
      } catch {
        setError("Erro ao carregar dados");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [fetchFunction]);

  return { data, loading, error };
}