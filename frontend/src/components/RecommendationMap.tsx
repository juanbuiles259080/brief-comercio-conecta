import type { NodeInfo, Recommendation } from '../types/domain';

type Props = {
  origin: NodeInfo;
  recs: Recommendation[];
  selected: string | null;
  onSelect: (id: string) => void;
};

// Medidas del dibujo (en unidades del viewBox).
const COL_W = 180;
const PILL_H = 36;
const PITCH = 48;
const TOP = 26;
const X_ORIGIN = 10;
const X_MID = 290;
const X_RIGHT = 570;

type Node = { id: string; name: string; x: number; y: number; kind: 'origin' | 'rec' | 'bridge'; recId?: string };
type Edge = { key: string; from: string; to: string; dashed: boolean };

function short(name: string): string {
  return name.length > 22 ? `${name.slice(0, 21)}…` : name;
}

/**
 * Dibujo de UNA consulta: producto elegido -> productos que se compran junto
 * con él -> productos relacionados. Solo contiene lo que devolvió la propuesta
 * (sin ids ni pesos): sirve para explicar por qué aparece cada recomendación.
 */
export function RecommendationMap({ origin, recs, selected, onSelect }: Props) {
  const directs = recs.filter(r => r.kind === 'direct');
  const indirects = recs.filter(r => r.kind === 'indirect');

  // Columna central: las recomendaciones directas y los productos puente.
  const mid: { id: string; name: string; recId?: string }[] = directs.map(r => ({
    id: r.product.id,
    name: r.product.name,
    recId: r.product.id,
  }));
  const midIds = new Set(mid.map(m => m.id));
  for (const r of indirects) {
    for (const v of r.via) {
      if (!midIds.has(v.id)) {
        midIds.add(v.id);
        mid.push({ id: v.id, name: v.name });
      }
    }
  }

  const rows = Math.max(mid.length, indirects.length, 1);
  const height = rows * PITCH + TOP;
  const width = indirects.length > 0 ? X_RIGHT + COL_W + 10 : X_MID + COL_W + 10;
  const yAt = (i: number, n: number) => TOP + (rows * PITCH - n * PITCH) / 2 + i * PITCH + (PITCH - PILL_H) / 2;

  const nodes: Node[] = [
    { id: origin.id, name: origin.name, x: X_ORIGIN, y: yAt(0, 1), kind: 'origin' },
    ...mid.map((m, i): Node => ({
      id: m.id, name: m.name, x: X_MID, y: yAt(i, mid.length), kind: m.recId ? 'rec' : 'bridge', recId: m.recId,
    })),
    ...indirects.map((r, i): Node => ({
      id: r.product.id, name: r.product.name, x: X_RIGHT, y: yAt(i, indirects.length), kind: 'rec', recId: r.product.id,
    })),
  ];
  const byId = new Map(nodes.map(n => [n.id, n]));

  const edges: Edge[] = [
    ...mid.map(m => ({ key: `o-${m.id}`, from: origin.id, to: m.id, dashed: false })),
    ...indirects.flatMap(r =>
      r.via.map(v => ({ key: `${v.id}-${r.product.id}`, from: v.id, to: r.product.id, dashed: true })),
    ),
  ];

  // Camino de la recomendación elegida.
  const sel = recs.find(r => r.product.id === selected) ?? null;
  const pathNodes = new Set<string>();
  const pathEdges = new Set<string>();
  if (sel) {
    pathNodes.add(origin.id);
    pathNodes.add(sel.product.id);
    if (sel.kind === 'direct') {
      pathEdges.add(`o-${sel.product.id}`);
    } else {
      for (const v of sel.via) {
        pathNodes.add(v.id);
        pathEdges.add(`o-${v.id}`);
        pathEdges.add(`${v.id}-${sel.product.id}`);
      }
    }
  }

  const curve = (a: Node, b: Node) => {
    const x1 = a.x + COL_W;
    const y1 = a.y + PILL_H / 2;
    const x2 = b.x;
    const y2 = b.y + PILL_H / 2;
    return `M ${x1} ${y1} C ${x1 + 55} ${y1}, ${x2 - 55} ${y2}, ${x2} ${y2}`;
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Cómo se conecta con <span className="text-emerald-700">{origin.name}</span>
      </h2>
      <p className="mt-1 text-sm text-slate-500">Toca una recomendación para ver su camino.</p>

      <div className="mt-4 overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          width={width}
          height={height}
          className="mx-auto block max-w-full"
          role="img"
          aria-label={`Mapa de conexiones de ${origin.name} con sus ${recs.length} recomendaciones`}
        >
          <g className="fill-slate-400 text-xs" fontSize="12" fontWeight="600">
            <text x={X_ORIGIN} y="14">Producto elegido</text>
            <text x={X_MID} y="14">Se compra junto</text>
            {indirects.length > 0 && <text x={X_RIGHT} y="14">Compra relacionada</text>}
          </g>

          {edges.map(e => {
            const a = byId.get(e.from);
            const b = byId.get(e.to);
            if (!a || !b) return null;
            const on = pathEdges.has(e.key);
            const dim = sel !== null && !on;
            return (
              <path
                key={e.key}
                d={curve(a, b)}
                fill="none"
                strokeWidth={on ? 3 : 1.5}
                strokeDasharray={e.dashed ? '5 4' : undefined}
                className={on ? 'stroke-emerald-600' : 'stroke-slate-300'}
                opacity={dim ? 0.35 : 1}
              />
            );
          })}

          {nodes.map(n => {
            const on = sel === null || pathNodes.has(n.id);
            const inPath = sel !== null && pathNodes.has(n.id);
            const clickable = n.kind === 'rec' && n.recId;
            const isOrigin = n.kind === 'origin';
            return (
              <g
                key={n.id}
                opacity={on ? 1 : 0.4}
                style={{ cursor: clickable ? 'pointer' : 'default' }}
                onClick={clickable ? () => onSelect(n.recId as string) : undefined}
              >
                <title>{n.name}</title>
                <rect
                  x={n.x}
                  y={n.y}
                  width={COL_W}
                  height={PILL_H}
                  rx="10"
                  strokeWidth={inPath ? 2.5 : 1.5}
                  strokeDasharray={n.kind === 'bridge' ? '4 3' : undefined}
                  className={
                    isOrigin
                      ? 'fill-emerald-700 stroke-emerald-700'
                      : inPath
                        ? 'fill-emerald-50 stroke-emerald-600'
                        : n.kind === 'bridge'
                          ? 'fill-slate-50 stroke-slate-300'
                          : 'fill-white stroke-slate-300'
                  }
                />
                <text
                  x={n.x + COL_W / 2}
                  y={n.y + PILL_H / 2 + 4.5}
                  textAnchor="middle"
                  fontSize="13"
                  fontWeight={isOrigin || inPath ? 600 : 400}
                  className={isOrigin ? 'fill-white' : 'fill-slate-800'}
                >
                  {short(n.name)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <p className="mt-3 text-xs text-slate-500">
        Línea continua: se compran juntos. Línea punteada: llegan a través de otro producto.
      </p>
    </div>
  );
}
