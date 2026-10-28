import { useEffect, useState } from 'react';
import { ApiError, api } from '../api/client';
import type { Exploration } from '../types/domain';

type State = {
  result: Exploration | null;
  loading: boolean;
  error: string | null;
};

/** Ejecuta el BFS del backend cada vez que cambia el origen, la profundidad o la red. */
export function useExplore(origin: string, depth: number, refreshTick = 0) {
  const [state, setState] = useState<State>({
    result: null,
    loading: false,
    error: null,
  });

  useEffect(() => {
    if (!origin) {
      setState({ result: null, loading: false, error: null });
      return;
    }
    let cancelled = false;
    setState(s => ({ ...s, loading: true }));
    api
      .explore(origin, depth)
      .then(result => {
        if (!cancelled) setState({ result, loading: false, error: null });
      })
      .catch(e => {
        if (cancelled) return;
        const msg = e instanceof ApiError ? e.detail : 'Error de red';
        setState({ result: null, loading: false, error: msg });
      });
    return () => {
      cancelled = true;
    };
  }, [origin, depth, refreshTick]);

  return state;
}
