-- Seed sintetico ComercioConecta (F1 T4)
-- 25 productos y 41 relaciones de co-compra.
-- Relaciones ya normalizadas (a < b alfabeticamente).
-- Los pesos representan "fuerza del vinculo" (co-compra observada):
--   1.0  = esperable; 1.5-2.0 = frecuente; 2.5-3.0 = casi siempre juntos.
-- INSERT OR IGNORE para que re-ejecuciones manuales no fallen.

-- ============== PRODUCTOS (25) ==============
INSERT OR IGNORE INTO products (id, name) VALUES
  ('aceite',          'Aceite de girasol'),
  ('agua',            'Agua mineral'),
  ('arroz',           'Arroz blanco'),
  ('atun',            'Atun en lata'),
  ('azucar',          'Azucar blanca'),
  ('cafe',            'Cafe molido'),
  ('cereal',          'Cereal de maiz'),
  ('cerveza',         'Cerveza lager'),
  ('detergente',      'Detergente ropa'),
  ('frijoles',        'Frijoles rojos'),
  ('galletas',        'Galletas dulces'),
  ('gaseosa',         'Gaseosa cola'),
  ('huevos',          'Huevos de granja'),
  ('jabon',           'Jabon de tocador'),
  ('jugo',            'Jugo de naranja'),
  ('leche',           'Leche entera'),
  ('mantequilla',     'Mantequilla'),
  ('mermelada',       'Mermelada de fresa'),
  ('pan',             'Pan de molde'),
  ('papel_higienico', 'Papel higienico'),
  ('pasta',           'Pasta espaguetti'),
  ('queso',           'Queso fresco'),
  ('sal',             'Sal de mesa'),
  ('salsa_tomate',    'Salsa de tomate'),
  ('yogur',           'Yogur natural');

-- ============== RELACIONES (41) ==============
-- Desayuno / pan y lacteos
INSERT OR IGNORE INTO relations (a, b, weight) VALUES
  ('leche',       'pan',          2.5),
  ('cafe',        'leche',        3.0),
  ('cereal',      'leche',        2.5),
  ('galletas',    'leche',        2.0),
  ('mantequilla', 'pan',          2.5),
  ('mermelada',   'pan',          2.0),
  ('pan',         'queso',        2.0),
  ('huevos',      'pan',          1.5),
  ('azucar',      'cafe',         2.5),
  ('cafe',        'galletas',     1.5),
  ('azucar',      'cereal',       1.0),
  ('cereal',      'yogur',        1.5),
  ('galletas',    'yogur',        1.5),
  ('azucar',      'yogur',        1.0);

-- Comida / almuerzo
INSERT OR IGNORE INTO relations (a, b, weight) VALUES
  ('arroz',        'frijoles',     3.0),
  ('aceite',       'arroz',        1.5),
  ('arroz',        'sal',          1.0),
  ('pasta',        'salsa_tomate', 3.0),
  ('aceite',       'pasta',        1.5),
  ('pasta',        'queso',        1.0),
  ('aceite',       'frijoles',     1.0),
  ('aceite',       'atun',         1.0),
  ('atun',         'pasta',        1.5),
  ('atun',         'salsa_tomate', 1.0),
  ('sal',          'salsa_tomate', 1.0),
  ('huevos',       'sal',          1.0),
  ('aceite',       'huevos',       1.5),
  ('mantequilla',  'sal',          1.0);

-- Bebidas
INSERT OR IGNORE INTO relations (a, b, weight) VALUES
  ('agua',    'gaseosa',  1.5),
  ('agua',    'jugo',     1.0),
  ('agua',    'cerveza',  1.0),
  ('galletas','gaseosa',  1.5),
  ('atun',    'gaseosa',  1.0),
  ('atun',    'queso',    1.0),
  ('gaseosa', 'pasta',    1.0),
  ('jugo',    'pan',      1.0),
  ('cereal',  'jugo',     1.0),
  ('galletas','jugo',     1.0);

-- Grupo separado: higiene / limpieza
-- (desconectado de la red de comestibles -> util para F2 componentes)
INSERT OR IGNORE INTO relations (a, b, weight) VALUES
  ('jabon',      'papel_higienico', 2.0),
  ('detergente', 'jabon',           1.5),
  ('detergente', 'papel_higienico', 1.5);
