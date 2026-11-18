import { useEffect, useMemo, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useNetwork } from '../hooks/useNetwork';

type Props = { refreshTick: number };

type VizNode = {
  id: string;
  name: string;
  color: string;
  x?: number;
  y?: number;
};

type VizLink = {
  source: string;
  target: string;
  weight: number;
};

function colorForId(id: string): string {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash * 31 + id.charCodeAt(i)) | 0;
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 65%, 50%)`;
}

export function GraphViz({ refreshTick }: Props) {
  const { network, loading, error } = useNetwork(refreshTick);
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(entries => {
      const entry = entries[0];
      if (entry) setWidth(entry.contentRect.width);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const data = useMemo(
    () => ({
      nodes: network.nodes.map(
        n =>
          ({
            id: n.id,
            name: n.name,
            color: colorForId(n.id),
          }) as VizNode,
      ),
      links: network.edges.map(
        e =>
          ({
            source: e.a,
            target: e.b,
            weight: e.weight,
          }) as VizLink,
      ),
    }),
    [network],
  );

  const sortedNodes = useMemo(
    () => [...network.nodes].sort((a, b) => a.id.localeCompare(b.id)),
    [network.nodes],
  );

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">Visualización de la red</h2>
        <span className="text-xs text-slate-500">
          Arrastrá nodos · scroll para zoom · hover para nombre completo
        </span>
      </div>

      <div
        ref={containerRef}
        className="h-[480px] w-full overflow-hidden rounded border border-slate-100 bg-slate-50"
      >
        {loading ? (
          <p className="p-4 text-sm text-slate-500">Cargando grafo...</p>
        ) : error ? (
          <p className="p-4 text-sm text-rose-600">{error}</p>
        ) : data.nodes.length === 0 ? (
          <p className="p-4 text-sm italic text-slate-500">
            Red vacía. Agregá productos y relaciones para visualizar.
          </p>
        ) : (
          <ForceGraph2D
            graphData={data}
            width={width}
            height={480}
            nodeLabel={(n: object) => (n as VizNode).name}
            nodeRelSize={6}
            linkWidth={(l: object) =>
              Math.max(1, (l as VizLink).weight * 1.2)
            }
            linkColor={() => 'rgba(100, 116, 139, 0.5)'}
            cooldownTicks={100}
            d3VelocityDecay={0.3}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const n = node as VizNode & { x: number; y: number };
              const r = 6;
              ctx.beginPath();
              ctx.arc(n.x, n.y, r, 0, 2 * Math.PI);
              ctx.fillStyle = n.color;
              ctx.fill();
              ctx.lineWidth = 1.5 / globalScale;
              ctx.strokeStyle = '#ffffff';
              ctx.stroke();
              const fontSize = Math.max(8, 10 / globalScale);
              ctx.font = `${fontSize}px sans-serif`;
              ctx.textAlign = 'center';
              ctx.textBaseline = 'top';
              ctx.fillStyle = '#0f172a';
              ctx.fillText(n.id, n.x, n.y + r + 2);
            }}
            nodePointerAreaPaint={(node, color, ctx) => {
              const n = node as VizNode & { x: number; y: number };
              ctx.beginPath();
              ctx.arc(n.x, n.y, 9, 0, 2 * Math.PI);
              ctx.fillStyle = color;
              ctx.fill();
            }}
          />
        )}
      </div>

      <p className="mt-2 text-xs text-slate-500">
        El grosor de cada arista representa la fuerza del vínculo (peso).
        Grupos desconectados quedan visualmente separados por el algoritmo de
        fuerza.
      </p>

      {sortedNodes.length > 0 && (
        <div className="mt-4">
          <h3 className="mb-2 text-sm font-medium text-slate-700">
            Leyenda ({sortedNodes.length} productos)
          </h3>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs md:grid-cols-3">
            {sortedNodes.map(n => (
              <div key={n.id} className="flex items-center gap-2">
                <span
                  className="inline-block h-3 w-3 flex-shrink-0 rounded-full border border-white shadow-sm"
                  style={{ backgroundColor: colorForId(n.id) }}
                  aria-hidden="true"
                />
                <span className="font-mono text-slate-800">{n.id}</span>
                <span className="truncate text-slate-500">{n.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
