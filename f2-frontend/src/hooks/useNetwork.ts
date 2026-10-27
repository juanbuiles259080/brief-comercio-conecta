import { useCallback, useEffect, useState } from 'react';
import { ApiError, api } from '../api/client';
import type { Network } from '../types/domain';

type State = {
  network: Network;
  loading: boolean;
  error: string | null;
};

const EMPTY: Network = { nodes: [], edges: [] };

export function useNetwork(refreshTick = 0) {
  const [state, setState] = useState<State>({
    network: EMPTY,
    loading: true,
    error: null,
  });

  const reload = useCallback(async () => {
    setState(s => ({ ...s, loading: true }));
    try {
      const network = await api.getNetwork();
      setState({ network, loading: false, error: null });
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : 'Error de red';
      setState(s => ({ ...s, loading: false, error: msg }));
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload, refreshTick]);

  return { ...state, reload };
}
