import { useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { ApiError, api } from '../api/client';
import { useNetwork } from '../hooks/useNetwork';
import { slugify } from '../lib/text';
import { ProductPicker } from './ProductPicker';

type Props = {
  refreshTick: number;
  onChange: () => void;
};

// Frecuencia en palabras de negocio -> peso interno (escala de seed.sql).
const FREQUENCIES = [
  { label: 'Ocasional', weight: 1.0, hint: 'Se llevan juntos a veces' },
  { label: 'Frecuente', weight: 2.0, hint: 'Se llevan juntos seguido' },
  { label: 'Casi siempre juntos', weight: 3.0, hint: 'Rara vez se compra uno sin el otro' },
] as const;

const input =
  'w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-base shadow-sm placeholder:text-slate-400 focus:border-emerald-600 focus:outline-none focus:ring-4 focus:ring-emerald-100';
const primary =
  'rounded-xl bg-emerald-700 px-5 py-2.5 font-medium text-white shadow-sm transition hover:bg-emerald-800 focus:outline-none focus:ring-4 focus:ring-emerald-200 disabled:opacity-50';

function labelForWeight(w: number): string {
  if (w >= 2.5) return 'Casi siempre juntos';
  if (w >= 1.5) return 'Frecuente';
  return 'Ocasional';
}

export function CatalogView({ refreshTick, onChange }: Props) {
  const { network } = useNetwork(refreshTick);

  const products = useMemo(
    () => [...network.nodes].sort((a, b) => a.name.localeCompare(b.name, 'es')),
    [network.nodes],
  );
  const names = useMemo(() => new Map(network.nodes.map(n => [n.id, n.name])), [network.nodes]);
  const purchases = useMemo(
    () =>
      network.edges
        .map(e => ({
          key: `${e.a}|${e.b}`,
          a: names.get(e.a) ?? e.a,
          b: names.get(e.b) ?? e.b,
          label: labelForWeight(e.weight),
        }))
        .sort((x, y) => x.a.localeCompare(y.a, 'es') || x.b.localeCompare(y.b, 'es')),
    [network.edges, names],
  );

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Catálogo y compras conjuntas</h1>
        <p className="mt-2 max-w-2xl text-lg text-slate-600">
          Aquí cargas la información que alimenta las recomendaciones: tus productos y cuáles se
          venden juntos.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <AddProductForm onChange={onChange} />
        <AddPurchaseForm products={products} onChange={onChange} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">
            Productos <span className="font-normal text-slate-500">({products.length})</span>
          </h2>
          {products.length === 0 ? (
            <p className="mt-3 text-slate-500">Todavía no hay productos. Agrega el primero arriba.</p>
          ) : (
            <ul className="mt-3 max-h-80 divide-y divide-slate-100 overflow-auto">
              {products.map(p => (
                <li key={p.id} className="py-2 text-slate-800">
                  {p.name}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">
            Compras conjuntas <span className="font-normal text-slate-500">({purchases.length})</span>
          </h2>
          {purchases.length === 0 ? (
            <p className="mt-3 text-slate-500">Todavía no hay compras conjuntas registradas.</p>
          ) : (
            <ul className="mt-3 max-h-80 divide-y divide-slate-100 overflow-auto">
              {purchases.map(p => (
                <li key={p.key} className="flex flex-wrap items-baseline justify-between gap-x-3 py-2">
                  <span className="text-slate-800">
                    {p.a} <span className="text-slate-400">+</span> {p.b}
                  </span>
                  <span className="text-sm text-slate-500">{p.label}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

function AddProductForm({ onChange }: { onChange: () => void }) {
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setOk(null);
    const clean = name.trim();
    const id = slugify(clean);
    if (!id) {
      setError('Escribe un nombre válido para el producto.');
      return;
    }
    setBusy(true);
    try {
      await api.createProduct({ id, name: clean });
      setOk(`“${clean}” se agregó al catálogo.`);
      setName('');
      onChange();
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 409
          ? 'Ya existe un producto con ese nombre.'
          : 'No se pudo agregar el producto. Revisa el nombre e intenta de nuevo.',
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Agregar un producto</h2>
      <label htmlFor="product-name" className="mt-4 mb-1.5 block text-sm font-medium text-slate-700">
        Nombre del producto
      </label>
      <input
        id="product-name"
        value={name}
        onChange={e => setName(e.target.value)}
        placeholder="Por ejemplo, Leche deslactosada"
        maxLength={200}
        required
        className={input}
      />
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button type="submit" disabled={busy} className={primary}>
          {busy ? 'Agregando…' : 'Agregar producto'}
        </button>
        <Feedback error={error} ok={ok} />
      </div>
    </form>
  );
}

function AddPurchaseForm({
  products,
  onChange,
}: {
  products: { id: string; name: string }[];
  onChange: () => void;
}) {
  const [a, setA] = useState('');
  const [b, setB] = useState('');
  const [weight, setWeight] = useState<number>(2.0);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setOk(null);
    if (!a || !b) {
      setError('Elige los dos productos.');
      return;
    }
    if (a === b) {
      setError('Elige dos productos distintos.');
      return;
    }
    setBusy(true);
    try {
      await api.createRelation({ a, b, weight });
      const nameA = products.find(p => p.id === a)?.name ?? a;
      const nameB = products.find(p => p.id === b)?.name ?? b;
      setOk(`Registrado: ${nameA} y ${nameB}.`);
      setA('');
      setB('');
      onChange();
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      setError(
        status === 409
          ? 'Esa compra conjunta ya está registrada.'
          : status === 404
            ? 'Uno de los productos ya no existe en el catálogo.'
            : 'No se pudo registrar. Revisa los datos e intenta de nuevo.',
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Registrar una compra conjunta</h2>
      <p className="mt-1 text-sm text-slate-500">Dos productos que los clientes llevan en la misma compra.</p>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <ProductPicker id="purchase-a" label="Primer producto" products={products} value={a} onChange={setA} />
        <ProductPicker id="purchase-b" label="Segundo producto" products={products} value={b} onChange={setB} />
      </div>

      <fieldset className="mt-5">
        <legend className="mb-1.5 text-sm font-medium text-slate-700">¿Qué tan seguido se compran juntos?</legend>
        <div className="grid gap-2 sm:grid-cols-3">
          {FREQUENCIES.map(f => (
            <label
              key={f.label}
              className={`cursor-pointer rounded-xl border px-3 py-2.5 text-sm transition ${
                weight === f.weight
                  ? 'border-emerald-600 bg-emerald-50 text-emerald-900'
                  : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
              }`}
            >
              <input
                type="radio"
                name="frequency"
                value={f.weight}
                checked={weight === f.weight}
                onChange={() => setWeight(f.weight)}
                className="sr-only"
              />
              <span className="block font-medium">{f.label}</span>
              <span className="block text-xs text-slate-500">{f.hint}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button type="submit" disabled={busy || products.length < 2} className={primary}>
          {busy ? 'Registrando…' : 'Registrar compra conjunta'}
        </button>
        <Feedback error={error} ok={ok} />
      </div>
      {products.length < 2 && (
        <p className="mt-3 text-sm text-slate-500">Necesitas al menos dos productos para registrar una compra conjunta.</p>
      )}
    </form>
  );
}

function Feedback({ error, ok }: { error: string | null; ok: string | null }) {
  if (error)
    return (
      <p role="alert" className="text-sm text-rose-700">
        {error}
      </p>
    );
  if (ok) return <p className="text-sm text-emerald-700">{ok}</p>;
  return null;
}
