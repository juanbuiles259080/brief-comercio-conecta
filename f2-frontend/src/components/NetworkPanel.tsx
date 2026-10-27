import { useMemo } from 'react';
import { useNetwork } from '../hooks/useNetwork';

type Props = { refreshTick: number };

type Neighbor = { id: string; name: string; weight: number };

export function NetworkPanel({ refreshTick }: Props) {
  const { network, loading, error } = useNetwork(refreshTick);

  const grouped = useMemo(() => {
    const nameById = new Map<string, string>();
    for (const n of network.nodes) nameById.set(n.id, n.name);

    const adj = new Map<string, Neighbor[]>();
    for (const n of network.nodes) adj.set(n.id, []);
    for (const e of network.edges) {
      adj.get(e.a)?.push({ id: e.b, name: nameById.get(e.b) ?? e.b, weight: e.weight });
      adj.get(e.b)?.push({ id: e.a, name: nameById.get(e.a) ?? e.a, weight: e.weight });
    }

    return [...network.nodes]
      .sort((x, y) => x.id.localeCompare(y.id))
      .map(n => ({
        id: n.id,
        name: n.name,
        neighbors: (adj.get(n.id) ?? []).sort((x, y) => y.weight - x.weight),
      }));
  }, [network]);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">Red</h2>
        <span className="text-xs text-slate-500">
          {network.nodes.length} nodos · {network.edges.length} aristas
        </span>
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Cargando...</p>
      ) : error ? (
        <p className="text-sm text-rose-600">{error}</p>
      ) : grouped.length === 0 ? (
        <p className="text-sm italic text-slate-500">
          Red vacía. Agregá productos y relaciones para empezar.
        </p>
      ) : (
        <ul className="space-y-2">
          {grouped.map(g => (
            <li
              key={g.id}
              className="rounded border border-slate-100 bg-slate-50 px-3 py-2"
            >
              <div className="flex items-baseline justify-between">
                <div>
                  <span className="font-mono text-sm font-semibold text-slate-800">
                    {g.id}
                  </span>
                  <span className="ml-2 text-xs text-slate-500">{g.name}</span>
                </div>
                <span className="text-xs text-slate-500">
                  {g.neighbors.length === 0
                    ? 'aislado'
                    : `${g.neighbors.length} ${g.neighbors.length === 1 ? 'vecino' : 'vecinos'}`}
                </span>
              </div>
              {g.neighbors.length > 0 && (
                <ul className="mt-1 flex flex-wrap gap-1.5">
                  {g.neighbors.map(n => (
                    <li
                      key={n.id}
                      className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-xs"
                      title={`${n.name} (peso ${n.weight})`}
                    >
                      <span className="font-mono">{n.id}</span>
                      <span className="ml-1 text-slate-500">
                        {n.weight.toFixed(1)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
