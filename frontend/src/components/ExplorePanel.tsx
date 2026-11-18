import { useMemo, useState } from 'react';
import { useExplore } from '../hooks/useExplore';
import { useNetwork } from '../hooks/useNetwork';
import type { Reached } from '../types/domain';

type Props = {
  refreshTick: number;
  origin: string;
  onOriginChange: (id: string) => void;
};

// Significado comercial de cada nivel (ver docs/decisiones.md, F2).
const LEVEL_LABEL: Record<number, string> = {
  1: 'Se compran juntos',
  2: 'Complemento del complemento',
  3: 'Relación lejana',
};

const DEPTH_HINT: Record<number, string> = {
  1: 'Solo compras directas',
  2: 'Recomendado',
  3: 'Tope: cubre gran parte del catálogo',
};

export function ExplorePanel({ refreshTick, origin, onOriginChange }: Props) {
  const { network } = useNetwork(refreshTick);
  const [depth, setDepth] = useState(2);
  const { result, loading, error } = useExplore(origin, depth, refreshTick);

  const products = useMemo(
    () => [...network.nodes].sort((a, b) => a.id.localeCompare(b.id)),
    [network.nodes],
  );
  const maxDepth = result?.max_depth ?? 3;

  const byLevel = useMemo(() => {
    const groups = new Map<number, Reached[]>();
    for (const r of result?.reached ?? []) {
      if (!groups.has(r.level)) groups.set(r.level, []);
      groups.get(r.level)!.push(r);
    }
    return [...groups.entries()].sort(([a], [b]) => a - b);
  }, [result]);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">Explorar relaciones</h2>
        <span className="text-xs text-slate-500">Recorrido BFS desde un producto</span>
      </div>

      <div className="mb-4 flex flex-wrap items-end gap-4">
        <div className="flex flex-col">
          <label htmlFor="explore-origin" className="text-xs text-slate-600">
            Producto de interés
          </label>
          <select
            id="explore-origin"
            value={origin}
            onChange={e => onOriginChange(e.target.value)}
            className="w-56 rounded border border-slate-300 px-2 py-1 text-sm focus:border-slate-500 focus:outline-none"
          >
            <option value="">— Elegí un producto —</option>
            {products.map(p => (
              <option key={p.id} value={p.id}>
                {p.id} · {p.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col">
          <span className="text-xs text-slate-600">Profundidad (saltos)</span>
          <div className="flex gap-1" role="group" aria-label="Profundidad">
            {Array.from({ length: maxDepth }, (_, i) => i + 1).map(d => (
              <button
                key={d}
                type="button"
                onClick={() => setDepth(d)}
                aria-pressed={depth === d}
                title={DEPTH_HINT[d]}
                className={`rounded border px-3 py-1 text-sm ${
                  depth === d
                    ? 'border-slate-900 bg-slate-900 text-white'
                    : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-100'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
        <span className="pb-1 text-xs text-slate-500">{DEPTH_HINT[depth]}</span>
      </div>

      {products.length === 0 ? (
        <p className="text-sm italic text-slate-500">
          Red vacía. Agregá productos y relaciones para explorar.
        </p>
      ) : !origin ? (
        <p className="text-sm italic text-slate-500">
          Elegí un producto para ver con qué se relaciona.
        </p>
      ) : loading && !result ? (
        <p className="text-sm text-slate-500">Explorando...</p>
      ) : error ? (
        <p className="text-sm text-rose-600">{error}</p>
      ) : result ? (
        <div className="space-y-4">
          <div
            className={`rounded border px-3 py-2 text-sm ${
              result.isolated
                ? 'border-amber-300 bg-amber-50 text-amber-900'
                : 'border-slate-200 bg-slate-50 text-slate-700'
            }`}
          >
            <span className="font-medium">{result.origin.name}:</span> {result.message}
          </div>

          {byLevel.map(([level, items]) => (
            <div key={level}>
              <h3 className="mb-1 text-sm font-medium text-slate-700">
                Nivel {level}{' '}
                <span className="font-normal text-slate-500">
                  · {LEVEL_LABEL[level] ?? ''} ({items.length})
                </span>
              </h3>
              <ul className="flex flex-wrap gap-1.5">
                {items.map(r => (
                  <li
                    key={r.id}
                    className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-xs"
                    title={`${r.name} — llegó por ${r.via} (peso ${r.weight})`}
                  >
                    <span className="font-mono">{r.id}</span>
                    <span className="ml-1 text-slate-500">
                      vía {r.via} · {r.weight.toFixed(1)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <details className="rounded border border-slate-100 bg-slate-50 px-3 py-2">
            <summary className="cursor-pointer text-sm font-medium text-slate-700">
              Traza del recorrido ({result.trace.length} pasos)
            </summary>
            <div className="mt-2 overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-left uppercase tracking-wide text-slate-500">
                    <th className="py-1 pr-3">Paso</th>
                    <th className="py-1 pr-3">Saco de la cola</th>
                    <th className="py-1 pr-3">Nivel</th>
                    <th className="py-1 pr-3">Descubre</th>
                    <th className="py-1">Ya visitados</th>
                  </tr>
                </thead>
                <tbody>
                  {result.trace.map(s => (
                    <tr key={s.step} className="border-b border-slate-100 align-top">
                      <td className="py-1 pr-3">{s.step}</td>
                      <td className="py-1 pr-3 font-mono">{s.node}</td>
                      <td className="py-1 pr-3">{s.level}</td>
                      <td className="py-1 pr-3 font-mono">
                        {s.expanded
                          ? s.discovered.join(', ') || '—'
                          : <span className="italic text-slate-400">límite, no se expande</span>}
                      </td>
                      <td className="py-1 font-mono text-slate-500">
                        {s.already_seen.join(', ') || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>
      ) : null}
    </section>
  );
}
