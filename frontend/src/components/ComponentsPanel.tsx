import { useComponents } from '../hooks/useComponents';

type Props = {
  refreshTick: number;
  onSelect: (id: string) => void;
};

export function ComponentsPanel({ refreshTick, onSelect }: Props) {
  const { data, loading, error } = useComponents(refreshTick);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">Grupos de productos</h2>
        <span className="text-xs text-slate-500">Componentes conexos</span>
      </div>

      {loading && data.count === 0 ? (
        <p className="text-sm text-slate-500">Cargando...</p>
      ) : error ? (
        <p className="text-sm text-rose-600">{error}</p>
      ) : data.count === 0 ? (
        <p className="text-sm italic text-slate-500">{data.message || 'Red vacía.'}</p>
      ) : (
        <>
          <p className="mb-3 text-sm text-slate-600">
            {data.message} Productos de grupos distintos nunca se relacionan entre sí.
          </p>
          <ul className="space-y-2">
            {data.components.map(c => (
              <li
                key={c.index}
                className={`rounded border px-3 py-2 ${
                  c.isolated
                    ? 'border-amber-200 bg-amber-50'
                    : 'border-slate-100 bg-slate-50'
                }`}
              >
                <div className="mb-1 flex items-baseline justify-between">
                  <span className="text-sm font-semibold text-slate-800">Grupo {c.index}</span>
                  <span className="text-xs text-slate-500">
                    {c.isolated
                      ? 'producto aislado'
                      : `${c.size} productos`}
                  </span>
                </div>
                <ul className="flex flex-wrap gap-1.5">
                  {c.products.map(p => (
                    <li key={p.id}>
                      <button
                        type="button"
                        onClick={() => onSelect(p.id)}
                        title={`Explorar desde ${p.name}`}
                        className="rounded-full border border-slate-200 bg-white px-2 py-0.5 font-mono text-xs hover:border-slate-500"
                      >
                        {p.id}
                      </button>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
