import { useCallback, useEffect, useState } from 'react';
import { ApiError, api } from '../api/client';
import type { Components } from '../types/domain';

type State = {
  data: Components;
  loading: boolean;
  error: string | null;
};

const EMPTY: Components = { count: 0, components: [], message: '' };

export function useComponents(refreshTick = 0) {
  const [state, setState] = useState<State>({
    data: EMPTY,
    loading: true,
    error: null,
  });

  const reload = useCallback(async () => {
    setState(s => ({ ...s, loading: true }));
    try {
      const data = await api.listComponents();
      setState({ data, loading: false, error: null });
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
