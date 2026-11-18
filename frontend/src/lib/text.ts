/** Minúsculas y sin tildes, para buscar "cafe" y encontrar "Café". */
export function normalize(s: string): string {
  return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

/** Identificador técnico a partir del nombre que escribe el usuario. */
export function slugify(name: string): string {
  return normalize(name)
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 64);
}
