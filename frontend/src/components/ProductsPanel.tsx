import { useState } from 'react';
import type { FormEvent } from 'react';
import { ApiError } from '../api/client';
import { useProducts } from '../hooks/useProducts';

type Props = {
  refreshTick: number;
  onChange: () => void;
};

export function ProductsPanel({ refreshTick, onChange }: Props) {
  const { products, loading, error, create } = useProducts(refreshTick);
  const [id, setId] = useState('');
  const [name, setName] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await create({ id: id.trim(), name: name.trim() });
      setId('');
      setName('');
      onChange();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.detail : 'Error desconocido');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">Productos</h2>
        <span className="text-xs text-slate-500">
          {products.length} {products.length === 1 ? 'producto' : 'productos'}
        </span>
      </div>

      <form
        onSubmit={handleSubmit}
        className="mb-4 flex flex-wrap items-end gap-3"
      >
        <div className="flex flex-col">
          <label htmlFor="prod-id" className="text-xs text-slate-600">
            ID
          </label>
          <input
            id="prod-id"
            value={id}
            onChange={e => setId(e.target.value)}
            placeholder="ej. leche"
            required
            className="w-40 rounded border border-slate-300 px-2 py-1 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div className="flex min-w-[200px] flex-1 flex-col">
          <label htmlFor="prod-name" className="text-xs text-slate-600">
            Nombre
          </label>
          <input
            id="prod-name"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="ej. Leche entera"
            required
            className="rounded border border-slate-300 px-2 py-1 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {submitting ? 'Agregando...' : 'Agregar'}
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
      ) : products.length === 0 ? (
        <p className="text-sm italic text-slate-500">Sin productos aun.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">ID</th>
                <th className="py-2 pr-4">Nombre</th>
                <th className="py-2">Creado</th>
              </tr>
            </thead>
            <tbody>
              {products.map(p => (
                <tr key={p.id} className="border-b border-slate-100">
                  <td className="py-2 pr-4 font-mono text-slate-800">{p.id}</td>
                  <td className="py-2 pr-4">{p.name}</td>
                  <td className="py-2 text-xs text-slate-500">
                    {p.created_at}
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
