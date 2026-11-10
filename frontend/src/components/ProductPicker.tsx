import { useMemo, useState } from 'react';
import type { KeyboardEvent } from 'react';
import { normalize } from '../lib/text';
import type { NodeInfo } from '../types/domain';

type Props = {
  id: string;
  label: string;
  products: NodeInfo[];
  value: string;
  onChange: (id: string) => void;
  placeholder?: string;
  large?: boolean;
};

/** Selector con búsqueda por nombre (sin tildes ni mayúsculas). */
export function ProductPicker({ id, label, products, value, onChange, placeholder, large }: Props) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);

  const selected = products.find(p => p.id === value);
  const filtered = useMemo(() => {
    const q = normalize(query);
    return products.filter(p => normalize(p.name).includes(q));
  }, [products, query]);

  function choose(p: NodeInfo) {
    onChange(p.id);
    setQuery('');
    setOpen(false);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setOpen(true);
      setActive(i => Math.min(i + 1, Math.max(filtered.length - 1, 0)));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive(i => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && open && filtered[active]) {
      e.preventDefault();
      choose(filtered[active]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  return (
    <div className="relative">
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={id}
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={`${id}-list`}
        aria-autocomplete="list"
        autoComplete="off"
        value={open ? query : (selected?.name ?? '')}
        placeholder={placeholder ?? 'Busca un producto…'}
        onFocus={() => {
          setOpen(true);
          setQuery('');
          setActive(0);
        }}
        onChange={e => {
          setQuery(e.target.value);
          setOpen(true);
          setActive(0);
        }}
        onBlur={() => setOpen(false)}
        onKeyDown={onKeyDown}
        className={`w-full rounded-xl border border-slate-300 bg-white px-4 text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-emerald-600 focus:outline-none focus:ring-4 focus:ring-emerald-100 ${
          large ? 'py-3.5 text-lg' : 'py-2.5 text-base'
        }`}
      />
      {open && (
        <ul
          id={`${id}-list`}
          role="listbox"
          className="absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
        >
          {filtered.length === 0 ? (
            <li className="px-4 py-3 text-sm text-slate-500">No encontramos ese producto.</li>
          ) : (
            filtered.map((p, i) => (
              <li
                key={p.id}
                role="option"
                aria-selected={p.id === value}
                onMouseDown={e => {
                  e.preventDefault();
                  choose(p);
                }}
                onMouseEnter={() => setActive(i)}
                className={`cursor-pointer px-4 py-2.5 text-base ${
                  i === active ? 'bg-emerald-50 text-emerald-900' : 'text-slate-800'
                } ${p.id === value ? 'font-semibold' : ''}`}
              >
                {p.name}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
