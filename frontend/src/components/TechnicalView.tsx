import { useState } from 'react';
import { ComponentsPanel } from './ComponentsPanel';
import { ExplorePanel } from './ExplorePanel';
import { GraphViz } from './GraphViz';
import { NetworkPanel } from './NetworkPanel';
import { ProductsPanel } from './ProductsPanel';
import { RelationsPanel } from './RelationsPanel';

type Props = {
  refreshTick: number;
  onChange: () => void;
};

/** Vista de equipo: grafo, recorridos y grupos (evidencia F1/F2 para pitch y revisión). */
export function TechnicalView({ refreshTick, onChange }: Props) {
  const [exploreOrigin, setExploreOrigin] = useState('');

  const exploreFrom = (id: string) => {
    setExploreOrigin(id);
    document.getElementById('explorar')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Vista técnica</h1>
        <p className="text-slate-600">
          Para el equipo de desarrollo: red de productos, recorridos y grupos. No forma parte de la experiencia del cliente.
        </p>
      </header>
      <GraphViz refreshTick={refreshTick} />
      <div id="explorar" className="scroll-mt-6">
        <ExplorePanel refreshTick={refreshTick} origin={exploreOrigin} onOriginChange={setExploreOrigin} />
      </div>
      <ComponentsPanel refreshTick={refreshTick} onSelect={exploreFrom} />
      <ProductsPanel refreshTick={refreshTick} onChange={onChange} />
      <RelationsPanel refreshTick={refreshTick} onChange={onChange} />
      <NetworkPanel refreshTick={refreshTick} />
    </div>
  );
}
