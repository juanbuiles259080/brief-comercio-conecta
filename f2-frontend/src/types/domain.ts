// Espejo de los schemas Pydantic del backend (ver backend/app/schemas.py).

export type Product = {
  id: string;
  name: string;
  created_at: string;
};

export type Relation = {
  a: string;
  b: string;
  weight: number;
};

export type NodeInfo = {
  id: string;
  name: string;
};

export type EdgeInfo = {
  a: string;
  b: string;
  weight: number;
};

export type Network = {
  nodes: NodeInfo[];
  edges: EdgeInfo[];
};

export type ProductIn = {
  id: string;
  name: string;
};

export type RelationIn = {
  a: string;
  b: string;
  weight?: number;
};

// ---------- Exploración (F2) ----------

export type Reached = {
  id: string;
  name: string;
  level: number;
  via: string;
  weight: number;
};

export type TraceStep = {
  step: number;
  node: string;
  level: number;
  discovered: string[];
  already_seen: string[];
  expanded: boolean;
};

export type Exploration = {
  origin: NodeInfo;
  depth: number;
  max_depth: number;
  isolated: boolean;
  truncated: boolean;
  reached: Reached[];
  trace: TraceStep[];
  message: string;
};

export type Component = {
  index: number;
  size: number;
  isolated: boolean;
  products: NodeInfo[];
};

export type Components = {
  count: number;
  components: Component[];
  message: string;
};

export type Health = {
  status: string;
  nodes: number;
  edges: number;
};
