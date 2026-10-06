import { useState } from 'react';
import { GraphViz } from './components/GraphViz';
import { NetworkPanel } from './components/NetworkPanel';
import { ProductsPanel } from './components/ProductsPanel';
import { RelationsPanel } from './components/RelationsPanel';

function App() {
  const [refreshTick, setRefreshTick] = useState(0);
  const bump = () => setRefreshTick(t => t + 1);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <header className="mb-8">
          <h1 className="text-3xl font-semibold">ComercioConecta</h1>
          <p className="text-slate-600">
            Red producto↔producto para una pyme de tiendas de barrio.
          </p>
        </header>

        <div className="space-y-6">
          <GraphViz refreshTick={refreshTick} />
          <ProductsPanel refreshTick={refreshTick} onChange={bump} />
          <RelationsPanel refreshTick={refreshTick} onChange={bump} />
          <NetworkPanel refreshTick={refreshTick} />
        </div>
      </div>
    </main>
  );
}

export default App;
