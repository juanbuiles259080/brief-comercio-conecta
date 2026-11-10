import { useMemo, useState } from 'react';
import { useNetwork } from '../hooks/useNetwork';
import { useRecommendations } from '../hooks/useRecommendations';
import { ProductPicker } from './ProductPicker';
import { RecommendationCard } from './RecommendationCard';

type Props = {
  refreshTick: number;
  onGoToCatalog: () => void;
};

const PAGE = 5;
const MAX = 10;

export function RecommendationsView({ refreshTick, onGoToCatalog }: Props) {
  const { network, loading: loadingCatalog } = useNetwork(refreshTick);
  const [origin, setOrigin] = useState('');
  const [limit, setLimit] = useState(PAGE);
  const { result, loading, error } = useRecommendations(origin, limit, refreshTick);

  const products = useMemo(
    () => [...network.nodes].sort((a, b) => a.name.localeCompare(b.name, 'es')),
    [network.nodes],
  );

  // Sugerencias rápidas: los productos con más compras conjuntas registradas.
  const suggestions = useMemo(() => {
    const degree = new Map<string, number>();
    for (const e of network.edges) {
      degree.set(e.a, (degree.get(e.a) ?? 0) + 1);
      degree.set(e.b, (degree.get(e.b) ?? 0) + 1);
    }
    return [...network.nodes]
      .filter(n => (degree.get(n.id) ?? 0) > 0)
      .sort((a, b) => (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0) || a.name.localeCompare(b.name, 'es'))
      .slice(0, 6);
  }, [network]);

  function pick(id: string) {
    setOrigin(id);
    setLimit(PAGE);
  }

  const hasMore = !!result && result.status === 'ok' && result.total_candidates > result.recommendations.length && limit < MAX;

  return (
    <div className="space-y-8">
      <section className="rounded-3xl bg-gradient-to-br from-slate-900 to-slate-800 px-6 py-10 text-white shadow-lg sm:px-10">
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          ¿Qué ofrecer junto con cada producto?
        </h1>
        <p className="mt-3 max-w-2xl text-lg text-slate-300">
          Elige un producto de tu tienda y te mostramos qué otros conviene proponer al cliente,
          con la razón de cada sugerencia.
        </p>

        <div className="mt-8 max-w-xl text-slate-900">
          {products.length > 0 ? (
            <ProductPicker
              id="origin"
              label="Producto de interés"
              products={products}
              value={origin}
              onChange={pick}
              placeholder="Escribe el nombre, por ejemplo “Leche”"
              large
            />
          ) : null}
        </div>

        {products.length > 0 && !origin && suggestions.length > 0 && (
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <span className="text-sm text-slate-400">Prueba con:</span>
            {suggestions.map(s => (
              <button
                key={s.id}
                type="button"
                onClick={() => pick(s.id)}
                className="rounded-full border border-white/20 bg-white/10 px-3.5 py-1.5 text-sm text-white transition hover:bg-white/20 focus:outline-none focus:ring-4 focus:ring-emerald-400/30"
              >
                {s.name}
              </button>
            ))}
          </div>
        )}
      </section>

      {loadingCatalog && products.length === 0 ? (
        <p className="text-center text-slate-500">Cargando catálogo…</p>
      ) : products.length === 0 ? (
        <EmptyState
          title="Aún no hay productos cargados"
          text="Para recibir recomendaciones, primero registra los productos y las compras conjuntas."
          action={{ label: 'Ir al catálogo', onClick: onGoToCatalog }}
        />
      ) : !origin ? (
        <p className="text-center text-slate-500">
          Selecciona un producto para ver sus recomendaciones.
        </p>
      ) : error ? (
        <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-5 text-rose-800">
          {error}
        </div>
      ) : loading && !result ? (
        <ul className="space-y-4" aria-busy="true" aria-label="Cargando recomendaciones">
          {[0, 1, 2].map(i => (
            <li key={i} className="h-28 animate-pulse rounded-2xl bg-slate-200/70" />
          ))}
        </ul>
      ) : result ? (
        result.status === 'isolated' ? (
          <EmptyState
            title={`Todavía no hay datos para ${result.origin.name}`}
            text={`${result.message} Cuando registres compras conjuntas de este producto, aquí aparecerán sus recomendaciones.`}
            action={{ label: 'Registrar compras conjuntas', onClick: onGoToCatalog }}
          />
        ) : (
          <section aria-live="polite" className={loading ? 'opacity-60 transition' : 'transition'}>
            <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
              <h2 className="text-xl font-semibold text-slate-900">
                Para quien lleva <span className="text-emerald-700">{result.origin.name}</span>, sugiere:
              </h2>
              <span className="text-sm text-slate-500">
                {result.recommendations.length} de {result.total_candidates}
              </span>
            </div>

            <ul className="space-y-4">
              {result.recommendations.map(rec => (
                <RecommendationCard key={rec.product.id} rec={rec} />
              ))}
            </ul>

            <p className="mt-4 rounded-xl bg-slate-100 px-4 py-3 text-sm text-slate-600">
              {result.message}
            </p>

            {hasMore && (
              <div className="mt-4 text-center">
                <button
                  type="button"
                  onClick={() => setLimit(MAX)}
                  className="rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-200"
                >
                  Ver más recomendaciones
                </button>
              </div>
            )}

            <details className="mt-8 rounded-2xl border border-slate-200 bg-white p-5">
              <summary className="cursor-pointer text-base font-medium text-slate-800">
                ¿Cómo se eligen estas recomendaciones?
              </summary>
              <div className="mt-3 space-y-3 text-slate-600">
                <p>{result.rule}</p>
                <ul className="list-disc space-y-1 pl-5 text-sm">
                  <li>
                    <strong>Se compra junto:</strong> hay compras conjuntas registradas con el producto elegido.
                  </li>
                  <li>
                    <strong>Compra relacionada:</strong> no se registra con el producto elegido, pero sí con otro
                    que lo acompaña; solo se muestra si ambos vínculos son frecuentes.
                  </li>
                  <li>
                    <strong>Límites:</strong> se basa solo en las compras conjuntas cargadas. No considera precio,
                    margen, inventario ni temporada, y favorece lo que ya se vende junto con más frecuencia.
                  </li>
                </ul>
              </div>
            </details>
          </section>
        )
      ) : null}
    </div>
  );
}

function EmptyState({
  title,
  text,
  action,
}: {
  title: string;
  text: string;
  action: { label: string; onClick: () => void };
}) {
  return (
    <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
      <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
      <p className="mx-auto mt-2 max-w-lg text-slate-600">{text}</p>
      <button
        type="button"
        onClick={action.onClick}
        className="mt-6 rounded-xl bg-emerald-700 px-5 py-2.5 font-medium text-white shadow-sm transition hover:bg-emerald-800 focus:outline-none focus:ring-4 focus:ring-emerald-200"
      >
        {action.label}
      </button>
    </div>
  );
}
