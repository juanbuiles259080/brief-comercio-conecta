import { useEffect, useState } from 'react';
import { ApiError, api } from '../api/client';
import type { Recommendations } from '../types/domain';

type State = {
  result: Recommendations | null;
  loading: boolean;
  error: string | null;
};

/** Pide la propuesta comercial cada vez que cambia el producto, el límite o los datos. */
export function useRecommendations(origin: string, limit: number, refreshTick = 0) {
  const [state, setState] = useState<State>({ result: null, loading: false, error: null });

  useEffect(() => {
    if (!origin) {
      setState({ result: null, loading: false, error: null });
      return;
    }
    let cancelled = false;
    setState(s => ({ ...s, loading: true }));
    api
      .recommendations(origin, limit)
      .then(result => {
        if (!cancelled) setState({ result, loading: false, error: null });
      })
      .catch(e => {
        if (cancelled) return;
        const msg =
          e instanceof ApiError && e.status === 404
            ? 'Ese producto ya no está en el catálogo.'
            : 'No pudimos obtener las recomendaciones. Intenta de nuevo en un momento.';
        setState({ result: null, loading: false, error: msg });
      });
    return () => {
      cancelled = true;
    };
  }, [origin, limit, refreshTick]);

  return state;
}
