import { useCallback, useEffect, useState } from 'react';
import { ApiError, api } from '../api/client';
import type { Relation, RelationIn } from '../types/domain';

type State = {
  relations: Relation[];
  loading: boolean;
  error: string | null;
};

export function useRelations(refreshTick = 0) {
  const [state, setState] = useState<State>({
    relations: [],
    loading: true,
    error: null,
  });

  const reload = useCallback(async () => {
    setState(s => ({ ...s, loading: true }));
    try {
      const relations = await api.listRelations();
      setState({ relations, loading: false, error: null });
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : 'Error de red';
      setState(s => ({ ...s, loading: false, error: msg }));
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload, refreshTick]);

  const create = useCallback((data: RelationIn) => api.createRelation(data), []);

  return { ...state, reload, create };
}
