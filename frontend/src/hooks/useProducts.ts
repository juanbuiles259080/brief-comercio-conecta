import { useCallback, useEffect, useState } from 'react';
import { ApiError, api } from '../api/client';
import type { Product, ProductIn } from '../types/domain';

type State = {
  products: Product[];
  loading: boolean;
  error: string | null;
};

export function useProducts(refreshTick = 0) {
  const [state, setState] = useState<State>({
    products: [],
    loading: true,
    error: null,
  });

  const reload = useCallback(async () => {
    setState(s => ({ ...s, loading: true }));
    try {
      const products = await api.listProducts();
      setState({ products, loading: false, error: null });
    } catch (e) {
      const msg = e instanceof ApiError ? e.detail : 'Error de red';
      setState(s => ({ ...s, loading: false, error: msg }));
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload, refreshTick]);

  // No recarga local: el llamador bumpea el tick global para que todo se refresque.
  const create = useCallback((data: ProductIn) => api.createProduct(data), []);

  return { ...state, reload, create };
}
