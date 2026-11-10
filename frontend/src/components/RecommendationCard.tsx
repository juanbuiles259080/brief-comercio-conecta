import type { Recommendation, StrengthLabel } from '../types/domain';

const LEVELS: Record<StrengthLabel, { bars: number; badge: string; bar: string }> = {
  'Casi siempre juntos': {
    bars: 3,
    badge: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
    bar: 'bg-emerald-600',
  },
  Frecuente: {
    bars: 2,
    badge: 'bg-amber-50 text-amber-800 ring-amber-200',
    bar: 'bg-amber-500',
  },
  Ocasional: {
    bars: 1,
    badge: 'bg-slate-100 text-slate-700 ring-slate-200',
    bar: 'bg-slate-400',
  },
};

export function RecommendationCard({ rec }: { rec: Recommendation }) {
  const level = LEVELS[rec.strength_label] ?? LEVELS.Ocasional;
  const direct = rec.kind === 'direct';

  return (
    <li className="flex gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white"
        aria-label={`Recomendación número ${rec.rank}`}
      >
        {rec.rank}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h3 className="text-lg font-semibold text-slate-900">{rec.product.name}</h3>
          <span
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset ${level.badge}`}
          >
            <span className="flex gap-0.5" aria-hidden="true">
              {[1, 2, 3].map(i => (
                <span
                  key={i}
                  className={`h-2.5 w-1.5 rounded-sm ${i <= level.bars ? level.bar : 'bg-black/10'}`}
                />
              ))}
            </span>
            {rec.strength_label}
          </span>
        </div>

        <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">
          {direct ? 'Se compra junto' : 'Compra relacionada'}
        </p>

        <p className="mt-2 text-base leading-relaxed text-slate-700">{rec.reason}</p>

        {!direct && rec.support > 1 && (
          <p className="mt-2 text-sm text-slate-500">
            Respaldada por {rec.support} productos en común.
          </p>
        )}
      </div>
    </li>
  );
}
