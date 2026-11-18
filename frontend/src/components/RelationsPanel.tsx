import { useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { ApiError } from '../api/client';
import { useProducts } from '../hooks/useProducts';
import { useRelations } from '../hooks/useRelations';

type Props = {
  refreshTick: number;
  onChange: () => void;
};

export function RelationsPanel({ refreshTick, onChange }: Props) {
  const { products } = useProducts(refreshTick);
  const { relations, loading, error, create } = useRelations(refreshTick);

  const [a, setA] = useState('');
  const [b, setB] = useState('');
  const [weight, setWeight] = useState('1.0');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const sortedProducts = useMemo(
    () => [...products].sort((x, y) => x.id.localeCompare(y.id)),
    [products],
  );

  const nameById = useMemo(() => {
    const m = new Map<string, string>();
    for (const p of products) m.set(p.id, p.name);
    return m;
  }, [products]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      const w = Number(weight);
      if (!Number.isFinite(w) || w <= 0) {
        throw new Error('El peso debe ser un número mayor a 0.');
      }
      await create({ a, b, weight: w });
      setA('');
      setB('');
      setWeight('1.0');
      onChange();
    } catch (err) {
      if (err instanceof ApiError) setFormError(err.detail);
      else if (err instanceof Error) setFormError(err.message);
      else setFormError('Error desconocido');
    } finally {
      setSubmitting(false);
    }
  }

  const canSubmit = a && b && a !== b && !submitting;

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">Relaciones de co-compra</h2>
        <span className="text-xs text-slate-500">
          {relations.length}{' '}
          {relations.length === 1 ? 'relación' : 'relaciones'}
        </span>
      </div>

      <div className="mb-4 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs leading-relaxed text-slate-600">
        <p>
          <strong className="text-slate-800">¿Qué es?</strong> Dos productos
          que se compran juntos frecuentemente en las tiendas.
        </p>
        <p className="mt-1">
          <strong className="text-slate-800">Peso</strong> (fuerza del vínculo):{' '}
          <span className="font-mono text-slate-800">1.0</span> ocasional ·{' '}
          <span className="font-mono text-slate-800">1.5-2.0</span> frecuente ·{' '}
          <span className="font-mono text-slate-800">2.5-3.0</span> casi
          siempre juntos.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="mb-4 flex flex-wrap items-end gap-3"
      >
        <div className="flex flex-col">
          <label htmlFor="rel-a" className="text-xs text-slate-600">
            Producto A
          </label>
          <select
            id="rel-a"
            value={a}
            onChange={e => setA(e.target.value)}
            required
            className="w-48 rounded border border-slate-300 bg-white px-2 py-1 text-sm focus:border-slate-500 focus:outline-none"
          >
            <option value="">— elegí —</option>
            {sortedProducts.map(p => (
              <option key={p.id} value={p.id}>
                {p.id} · {p.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col">
          <label htmlFor="rel-b" className="text-xs text-slate-600">
            Producto B
          </label>
          <select
            id="rel-b"
            value={b}
            onChange={e => setB(e.target.value)}
            required
            className="w-48 rounded border border-slate-300 bg-white px-2 py-1 text-sm focus:border-slate-500 focus:outline-none"
          >
            <option value="">— elegí —</option>
            {sortedProducts.map(p => (
              <option key={p.id} value={p.id}>
                {p.id} · {p.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col">
          <label htmlFor="rel-weight" className="text-xs text-slate-600">
            Peso (fuerza del vínculo)
          </label>
          <input
            id="rel-weight"
            type="number"
            step="0.1"
            min="0.1"
            value={weight}
            onChange={e => setWeight(e.target.value)}
            required
            className="w-24 rounded border border-slate-300 px-2 py-1 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={!canSubmit}
          className="rounded bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {submitting ? 'Creando...' : 'Crear relación'}
        </button>
      </form>

      {formError && (
        <div className="mb-4 rounded border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {formError}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Cargando...</p>
      ) : error ? (
        <p className="text-sm text-rose-600">{error}</p>
      ) : relations.length === 0 ? (
        <p className="text-sm italic text-slate-500">Sin relaciones aun.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">A</th>
                <th className="py-2 pr-4">B</th>
                <th className="py-2">Peso</th>
              </tr>
            </thead>
            <tbody>
              {relations.map(r => (
                <tr
                  key={`${r.a}-${r.b}`}
                  className="border-b border-slate-100"
                >
                  <td className="py-2 pr-4">
                    <span className="font-mono text-slate-800">{r.a}</span>
                    <span className="ml-2 text-xs text-slate-500">
                      {nameById.get(r.a) ?? ''}
                    </span>
                  </td>
                  <td className="py-2 pr-4">
                    <span className="font-mono text-slate-800">{r.b}</span>
                    <span className="ml-2 text-xs text-slate-500">
                      {nameById.get(r.b) ?? ''}
                    </span>
                  </td>
                  <td className="py-2 font-mono text-slate-700">
                    {r.weight.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
