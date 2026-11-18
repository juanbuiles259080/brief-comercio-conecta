import { useState } from 'react';
import { CatalogView } from './components/CatalogView';
import { RecommendationsView } from './components/RecommendationsView';
import { TechnicalView } from './components/TechnicalView';

type View = 'recomendaciones' | 'catalogo' | 'tecnico';

const NAV: { id: Exclude<View, 'tecnico'>; label: string }[] = [
  { id: 'recomendaciones', label: 'Recomendaciones' },
  { id: 'catalogo', label: 'Catálogo' },
];

function App() {
  const [view, setView] = useState<View>('recomendaciones');
  // Cualquier cambio de datos refresca todas las vistas (ver docs/decisiones.md).
  const [refreshTick, setRefreshTick] = useState(0);
  const bump = () => setRefreshTick(t => t + 1);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900 antialiased">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-6 py-4">
          <button
            type="button"
            onClick={() => setView('recomendaciones')}
            className="flex items-center gap-2.5 rounded-lg focus:outline-none focus:ring-4 focus:ring-emerald-100"
          >
            <span
              aria-hidden="true"
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-700 text-lg font-bold text-white"
            >
              C
            </span>
            <span className="text-xl font-semibold tracking-tight">ComercioConecta</span>
          </button>

          <nav aria-label="Principal" className="flex gap-1">
            {NAV.map(item => (
              <button
                key={item.id}
                type="button"
                onClick={() => setView(item.id)}
                aria-current={view === item.id ? 'page' : undefined}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition focus:outline-none focus:ring-4 focus:ring-emerald-100 ${
                  view === item.id
                    ? 'bg-emerald-50 text-emerald-800'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
        {view === 'recomendaciones' && (
          <RecommendationsView refreshTick={refreshTick} onGoToCatalog={() => setView('catalogo')} />
        )}
        {view === 'catalogo' && <CatalogView refreshTick={refreshTick} onChange={bump} />}
        {view === 'tecnico' && <TechnicalView refreshTick={refreshTick} onChange={bump} />}
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4 text-sm text-slate-500">
          <span>ComercioConecta · Recomendaciones de productos para tiendas de barrio</span>
          <button
            type="button"
            onClick={() => setView(view === 'tecnico' ? 'recomendaciones' : 'tecnico')}
            className="rounded px-2 py-1 text-slate-400 hover:text-slate-700 focus:outline-none focus:ring-4 focus:ring-slate-100"
          >
            {view === 'tecnico' ? 'Salir de la vista técnica' : 'Vista técnica'}
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;
