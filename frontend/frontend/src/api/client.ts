import type {
  Health,
  Network,
  Product,
  ProductIn,
  Relation,
  RelationIn,
} from '../types/domain';

const BASE =
  (import.meta.env.VITE_API_URL as string | undefined) ??
  'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

type PydanticIssue = {
  loc?: (string | number)[];
  msg?: string;
};

function formatDetail(body: unknown): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return (detail as PydanticIssue[])
        .map(issue => {
          const loc = issue.loc?.join('.') ?? '';
          return loc ? `${loc}: ${issue.msg ?? '?'}` : issue.msg ?? '?';
        })
        .join('; ');
    }
    return JSON.stringify(detail);
  }
  return JSON.stringify(body);
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = formatDetail(await res.json());
    } catch {
      /* body no era JSON */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  listProducts: () => call<Product[]>('/products'),
  getProduct: (id: string) =>
    call<Product>(`/products/${encodeURIComponent(id)}`),
  createProduct: (data: ProductIn) =>
    call<Product>('/products', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  listRelations: () => call<Relation[]>('/relations'),
  createRelation: (data: RelationIn) =>
    call<Relation>('/relations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getNetwork: () => call<Network>('/network'),
  health: () => call<Health>('/health'),
};
