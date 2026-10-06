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

export type Health = {
  status: string;
  nodes: number;
  edges: number;
};
