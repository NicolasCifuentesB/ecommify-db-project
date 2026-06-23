# Ecommify — Arquitectura Híbrida de Persistencia Políglota

**Grupo E25 | Diseño y Optimización de Bases de Datos — MAS 2026-3 G1G2**  
Maestría en Arquitectura de Software · Universidad de La Sabana · Docente: Miguel Alfonso Varela · 2026

**Integrantes:** Andres Camilo Meneses Ortega · David Hernando Monsalve Delima · Eduardo Trujillo Santos · Nicolás Cifuentes Barriga

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17.6-336791)
![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-7.0-47A248)
![Supabase](https://img.shields.io/badge/Supabase-Free_Tier-3ECF8E)
![Dataset](https://img.shields.io/badge/Dataset-Olist_99k_orders-orange)

---

## Descripción del Proyecto

Ecommify es una plataforma de e-commerce que implementa una **arquitectura híbrida de persistencia políglota**: PostgreSQL (Supabase) gestiona el núcleo transaccional con garantías ACID y MongoDB Atlas gestiona el catálogo de productos y la analítica de reseñas con consistencia eventual.

La elección de base de datos se hace **módulo a módulo** según el Teorema CAP: PostgreSQL = CP (Consistency + Partition Tolerance) para pagos y pedidos; MongoDB = AP (Availability + Partition Tolerance) para catálogo y analítica.

**Dataset:** Olist Brazilian E-Commerce (Kaggle, 2018) — 99,441 pedidos · 112,650 ítems · 1,000 productos MongoDB · 3,118 reseñas · infraestructura 100% cloud gratuita.

---

## Resultados Clave

| Operación | Antes | Después | Mejora |
|-----------|-------|---------|--------|
| MongoDB Q1 catálogo ESR | 1,000 docsExamined | 328 | **−67.2%** |
| MongoDB Attribute Pattern (`material=silicone`) | 1,000 docsExamined | 8 | **−99.2%** |
| MongoDB Bucket Pattern (reviews) | 3,118 documentos | 954 buckets | **−69.4%** |
| PostgreSQL Q4 pedidos pendientes | 13.85 ms | 1.01 ms | **−92.7%** |
| PostgreSQL Q7 entregas por estado | 378.03 ms | 91.68 ms | **−75.8%** |
| PostgreSQL Q2 partition pruning | 1,180 ms | 21.75 ms | **−98.2%** |

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                        ECOMMIFY PLATFORM                         │
│                    (Application Server Layer)                    │
├────────────────────────────┬─────────────────────────────────────┤
│   PostgreSQL (Supabase)    │         MongoDB Atlas M0             │
│   Clasificación: CP        │         Clasificación: AP            │
├────────────────────────────┼─────────────────────────────────────┤
│ customers     (99,441)     │ products        (1,000 docs)         │
│ orders        (99,441)     │   └─ Attribute Pattern [{k,v}]       │
│ order_items  (112,650)     │   └─ Extended Reference (seller_info)│
│ payments     (103,877)     │   └─ Índices ESR compuestos          │
│ sellers        (3,095)     │ reviews         (3,118 docs)         │
│ geolocations  (19,015)     │   └─ $jsonSchema validationLevel     │
│                            │   └─ Índice parcial score ≤ 2        │
│ Optimizaciones:            │ reviews_buckets   (954 buckets)      │
│ • GENERATED ALWAYS AS      │   └─ Bucket Pattern (analítica O(1)) │
│ • GIN / GiST / BRIN        │   └─ Reconstrucción vía $out         │
│ • Partición RANGE por año  │                                      │
│ • Índices parciales        │ Shard key: category.english + _id    │
│ • pg_trgm / PostGIS        │ Dist. shards: 33.4% / 33.3% / 33.3% │
└────────────────────────────┴─────────────────────────────────────┘
                              ↑ Caché Redis (prod): TTL catálogo 5min
```

### Decisión de partición por módulo

| Módulo | Base de Datos | Clasificación CAP | Razón principal |
|--------|--------------|-------------------|-----------------|
| orders / payments | PostgreSQL | **CP** | ACID crítico — pago no puede quedar indeterminado |
| order_items | PostgreSQL | **CP** | Atomicidad con orders vía FK; GENERATED total_amount |
| customers | PostgreSQL | **CP** | FK con órdenes; search_vector GENERATED (tsvector) |
| geolocations | PostgreSQL | **CP** | PostGIS; JOIN con customers por zip_code_prefix |
| products (catálogo) | MongoDB | **AP** | Specs variables por categoría; schema-less requerido |
| reviews | MongoDB | **AP** | Alta tasa de inserción; consistencia eventual aceptable |
| reviews_buckets | MongoDB | **AP** | Analítica temporal; reconstrucción periódica vía `$out` |

---

## Estructura del Repositorio

```
ecommify-db-project/
│
├── postgresql/
│   ├── schema/
│   │   ├── extensions.psql      # pg_trgm, PostGIS, uuid-ossp — ejecutar primero
│   │   ├── schema.psql          # DDL principal: tablas, constraints, tipos avanzados
│   │   ├── tables.psql          # Definición detallada con GENERATED y JSONB
│   │   ├── triggers.psql        # fn_update_search_vector(), updated_at automático
│   │   ├── index.psql           # Índices B-tree, GIN, GiST, BRIN, parciales
│   │   └── partitions.psql      # Particionamiento RANGE por purchase_timestamp
│   ├── queries/
│   │   └── fill_tables.psql     # Carga del dataset Olist desde CSVs
│   └── seed_data/               # Dataset Olist Brazilian E-Commerce (Kaggle 2018)
│       ├── olist_orders_dataset.csv
│       ├── olist_customers_dataset.csv
│       ├── olist_order_items_dataset.csv
│       ├── olist_order_payments_dataset.csv
│       ├── olist_order_reviews_dataset.csv
│       ├── olist_products_dataset.csv
│       ├── olist_sellers_dataset.csv
│       ├── olist_geolocation_dataset.csv
│       └── product_category_name_translation.csv
│
├── mongodb/
│   └── schema/
│       ├── create.py            # Creación de colecciones con $jsonSchema
│       ├── products.py          # Modelado: Attribute Pattern + Extended Reference
│       ├── reviews.py           # Reseñas individuales con validación de esquema
│       ├── index.py             # Índices ESR, parciales, text, bucket
│       ├── analytic_pipeline.py # Aggregation pipeline de 7 stages ($match temprano)
│       ├── validation.py        # Reglas $jsonSchema (validationLevel=moderate)
│       ├── analytics.py         # Colección de analítica agregada
│       ├── carts.py             # Carritos con TTL index
│       ├── recommendations.py   # Motor de recomendaciones
│       └── product_views.py     # Registro de vistas de producto
│
├── notebooks/                   # Ejecutar en orden U1 → U6 (Google Colab o Jupyter)
│   ├── U1 - Analisis exploratorio.ipynb       # EDA del dataset Olist
│   ├── U2 - Tipos Avanzados.ipynb             # PostgreSQL: GENERATED, JSONB, PostGIS, pg_trgm
│   ├── U3 - MongoDB Ecommify.ipynb            # Modelado con patrones de diseño
│   ├── U4 - Optimizacion Implementacion.ipynb # Índices PG y particionamiento RANGE
│   ├── U5 - Optimizacion MongoDB.ipynb        # ESR, Bucket, Atlas Search, sharding
│   ├── U6 - Performance Tests.ipynb           # Benchmarks, comparativo PG vs MDB, CAP
│   └── fig1_load_test.png … fig6_*.png        # Gráficas generadas por U6
│
└── docs/
    ├── U5 - E25 Informe Final Integral.docx   # Informe técnico final (entrega U6)
    ├── U4 - E25 Optimizacion Particionamiento Ecommify.pdf
    ├── Presentación ecommify.pdf
    └── [Guías de actividades por unidad]
```

---

## Requisitos Previos

- Python **3.10+**
- Cuenta **Supabase** gratuita — [supabase.com](https://supabase.com)
- Cuenta **MongoDB Atlas** gratuita (cluster M0) — [mongodb.com/atlas](https://www.mongodb.com/atlas)
- Google Colab **o** Jupyter Notebook local

> Los notebooks incluyen `!pip install ...` en su primera celda — no se requiere instalación previa para Colab.

---

## Setup Completo

### 1. Clonar el repositorio

```bash
git clone https://github.com/<usuario>/ecommify-db-project.git
cd ecommify-db-project
```

### 2. Variables de entorno

Crear un archivo `.env` en la raíz del proyecto (nunca subir al repositorio):

```env
# PostgreSQL — Supabase
# Usar Transaction Pooler (puerto 6543) para producción con pgBouncer
DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# MongoDB Atlas
MONGO_URI=mongodb+srv://<user>:<password>@clustermaestriadb.qibjniy.mongodb.net/?appName=ClusterMaestriaDB
```

> **Dónde obtener `DATABASE_URL`:** Supabase → Project → Settings → Database → Connection string → Transaction Pooler  
> **Dónde obtener `MONGO_URI`:** Atlas → Connect → Drivers → Python

### 3. Setup PostgreSQL (Supabase)

Ejecutar los scripts DDL **en el siguiente orden** desde el SQL Editor de Supabase o con `psql`:

```bash
# Instalar cliente psql si es necesario
pip install psycopg2-binary

# 1. Extensiones (pg_trgm, PostGIS, uuid-ossp)
psql $DATABASE_URL -f postgresql/schema/extensions.psql

# 2. Esquema principal (tablas, tipos, constraints, GENERATED columns)
psql $DATABASE_URL -f postgresql/schema/schema.psql
psql $DATABASE_URL -f postgresql/schema/tables.psql

# 3. Triggers (search_vector, updated_at)
psql $DATABASE_URL -f postgresql/schema/triggers.psql

# 4. Particionamiento RANGE por purchase_timestamp
psql $DATABASE_URL -f postgresql/schema/partitions.psql

# 5. Índices (B-tree, GIN, GiST, BRIN, parciales)
psql $DATABASE_URL -f postgresql/schema/index.psql

# 6. Carga de datos Olist desde seed_data/
psql $DATABASE_URL -f postgresql/queries/fill_tables.psql
```

**Verificar setup:**
```sql
-- En Supabase SQL Editor
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
-- Resultado esperado: orders (99,441 filas), order_items (112,650), customers (99,441)
```

### 4. Setup MongoDB (Atlas)

```bash
# Instalar dependencias Python
pip install pymongo pandas matplotlib seaborn tabulate

# Crear colecciones con validación $jsonSchema
python mongodb/schema/create.py

# Modelado de productos (Attribute Pattern + Extended Reference)
python mongodb/schema/products.py

# Modelado de reseñas con validación
python mongodb/schema/reviews.py

# Crear todos los índices (ESR, parciales, text, bucket)
python mongodb/schema/index.py

# Construir reviews_buckets (Bucket Pattern: 3,118 → 954 docs)
python mongodb/schema/analytic_pipeline.py
```

**Verificar setup:**
```python
from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI"))
db = client["ecommify"]
print(f"products:        {db.products.count_documents({}):,}")         # → 1,000
print(f"reviews:         {db.reviews.count_documents({}):,}")          # → 3,118
print(f"reviews_buckets: {db.reviews_buckets.count_documents({}):,}")  # → 954
print(f"Índices products: {db.products.index_information().keys()}")
```

### 5. Ejecutar notebooks

Los notebooks están diseñados para **Google Colab** (recomendado) o Jupyter local. Ejecutar en orden:

| Notebook | Contenido | Colab |
|----------|-----------|-------|
| `U1 - Analisis exploratorio.ipynb` | EDA del dataset Olist, distribuciones, correlaciones | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/) |
| `U2 - Tipos Avanzados.ipynb` | GENERATED, JSONB, PostGIS, pg_trgm en PostgreSQL | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/) |
| `U3 - MongoDB Ecommify.ipynb` | Modelado con Attribute, Extended Reference, Bucket Pattern | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/) |
| `U4 - Optimizacion Implementacion.ipynb` | Índices PG, particionamiento RANGE, benchmarks | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/) |
| `U5 - Optimizacion MongoDB.ipynb` | ESR, Bucket Pattern, Atlas Search, sharding simulado | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/) |
| `U6 - Performance Tests.ipynb` | Benchmarks de carga, comparativo PG vs MDB, análisis CAP | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/) |

> Cada notebook instala sus dependencias automáticamente en la primera celda (`%%capture / !pip install ...`). Solo se requiere configurar `MONGO_URI` y `DATABASE_URL` como variables de entorno o directamente en la celda de conexión.

**Jupyter local:**
```bash
pip install jupyter pymongo psycopg2-binary pandas matplotlib seaborn tabulate
jupyter notebook notebooks/
```

---

## Teorema CAP — Configuraciones por Módulo

| Módulo | BD | CAP | Configuración específica |
|--------|----|-----|--------------------------|
| orders / payments | PostgreSQL | **CP** | `synchronous_commit=on` · `SERIALIZABLE` · FK con customers |
| order_items | PostgreSQL | **CP** | FK con orders · `GENERATED total_amount` · atomicidad garantizada |
| customers | PostgreSQL | **CP** | `search_vector` GENERATED · FK con órdenes · integridad referencial |
| orders (particionado) | PostgreSQL | **CP** | BRIN en `purchase_timestamp` · partition pruning automático |
| products (catálogo) | MongoDB | **AP** | `readPreference=secondaryPreferred` · replication lag 1–5s aceptable |
| reviews | MongoDB | **AP** | `writeConcern={w:1, j:false}` · throughput priorizado |
| reviews_buckets | MongoDB | **AP** | Reconstrucción periódica vía `$out` · consistencia eventual intencional |

**Comportamiento ante network partitions:**
- **PostgreSQL (CP):** el primary rechaza escrituras sin confirmación de réplica (`synchronous_commit=on`). Ventana de indisponibilidad de 10–30s hasta nuevo líder. Ninguna orden queda duplicada o inconsistente.
- **MongoDB (AP):** el catálogo y las reseñas permanecen accesibles con `w:1`. Los buckets pueden estar hasta 1 período desactualizados — conocido y aceptado.

---

## Índices Implementados

### PostgreSQL

| Nombre | Tipo | Tabla | Impacto medido |
|--------|------|-------|----------------|
| `idx_orders_status_ts` | B-tree compuesto | orders | Elimina Sort explícito en Q1/Q2 |
| `idx_orders_active_partial` | Parcial (0.3% filas) | orders | Q4: 13.85 ms → 1.01 ms (−92.7%) |
| `idx_orders_purchase_brin` | BRIN | orders | 24 KB vs ~50 MB B-tree (>2,000x más compacto) |
| `idx_items_seller_price` | B-tree compuesto | order_items | Q6: Index Only Scan posible |
| `idx_orders_shipping_gin` | GIN (jsonb_path_ops) | orders | Búsqueda JSONB `@>` en shipping_address |
| `idx_customers_search` | GiST (pg_trgm) | customers | Búsqueda fuzzy en customer_city |

### MongoDB

| Nombre | Tipo | Colección | Impacto medido |
|--------|------|-----------|----------------|
| `idx_esr_active_rating_price` | ESR compuesto | products | 1,000 → 328 docsExamined (−67.2%) |
| `idx_esr_active_category_sold` | ESR compuesto | products | Catálogo por categoría + sort ventas |
| `idx_attribute_pattern_specs` | Compuesto sobre array | products | 1,000 → 8 docsExamined (−99.2%) |
| `idx_partial_active_high_rating` | Parcial (activos, rating ≥ 4.0) | products | ~40% más pequeño que índice completo |
| `idx_text_products` | Atlas Search (Lucene) | products | Full-text ponderado: name×10, tags×5, category×3 |
| `idx_bucket_product_month` | Compuesto | reviews_buckets | Analítica temporal O(1) por período |
| `idx_partial_low_score_reviews` | Parcial (score ≤ 2) | reviews | Atención al cliente en tiempo real |

---

## Score Comparativo PostgreSQL vs MongoDB (12 aspectos)

| Aspecto | PG | MDB | Ganador | Evidencia del proyecto |
|---------|:--:|:---:|---------|------------------------|
| Consultas transaccionales (ACID) | 9 | 5 | **PostgreSQL** | Multi-doc transactions en MDB: overhead 3–5x |
| Flexibilidad de esquema | 6 | 9 | **MongoDB** | Specs variables por categoría — schema-less requerido |
| Índices compuestos ESR | 8 | 9 | **MongoDB** | Q1: 1,000→328 docsExamined (−67.2%) |
| Integridad referencial (FK) | 10 | 4 | **PostgreSQL** | FK declarativas, CASCADE, GENERATED. MDB: manual |
| Analítica de reviews (temporal) | 5 | 9 | **MongoDB** | Bucket: 3,118→954 docs (−69.4%), O(1) por período |
| Escalabilidad horizontal | 5 | 9 | **MongoDB** | Shard key diseñada: 33.4% / 33.3% / 33.3% (3 shards) |
| Consistencia (ACID vs eventual) | 9 | 6 | **PostgreSQL** | PG: consistencia fuerte por defecto |
| Patrones de diseño embebido | 4 | 9 | **MongoDB** | Extended Reference elimina `$lookup` en hot path |
| Búsqueda full-text | 7 | 9 | **MongoDB** | Atlas Search con pesos diferenciados ya implementado |
| Índices especializados | 8 | 7 | **PostgreSQL** | GIN, GiST, BRIN (100x más compacto que B-tree) |
| Validación de esquema | 9 | 7 | **PostgreSQL** | `$jsonSchema` potente pero manual vs CHECK nativo |
| Monitoreo / observabilidad | 8 | 8 | **Empate** | `pg_stat_statements` ↔ Atlas Performance Advisor |

**Resultado: PostgreSQL 5 victorias · MongoDB 6 victorias · 1 Empate**

> La ventaja de MongoDB se concentra exactamente en los módulos donde Ecommify tiene mayor volumen y variabilidad: catálogo y analítica de reseñas. La arquitectura híbrida es la consecuencia natural de esta evidencia empírica.

---

## Tecnologías

| Capa | Tecnología | Versión | Uso |
|------|-----------|---------|-----|
| BD Relacional | PostgreSQL | 17.6 | Core transaccional + analítica estructurada |
| BD Documental | MongoDB Atlas | 7.0 | Catálogo flexible + analítica de reseñas |
| Hosting PG | Supabase | Free tier | pgBouncer + REST API + SQL Editor |
| Hosting MDB | Atlas M0 | Free tier | Cluster + Performance Advisor + Atlas Search |
| Lenguaje | Python | 3.12 | Notebooks, ETL, benchmarks, scripts de setup |
| Visualización | Matplotlib / Seaborn | latest | 6 gráficas de rendimiento (U6) |
| Dataset | Olist Brazilian E-Commerce | 2018 | 99,441 pedidos reales — Kaggle |

---

## Plan de Escalamiento 10x (Free Tier → Producción)

| Componente | Estado actual | Target producción | Costo aprox. |
|------------|--------------|-------------------|-------------|
| MongoDB | Atlas M0 (512MB, shared) | Atlas M10 (2GB dedicado) | ~$57/mes |
| PostgreSQL | Supabase Free (500MB, 15 conex.) | Supabase Pro + pgBouncer | ~$25/mes |
| Caché | Sin caché externo | Redis Cloud Essentials 250MB | ~$0–5/mes |
| Observabilidad | Atlas Advisor + Supabase logs | Datadog APM / Grafana Cloud | variable |

**Cambios técnicos requeridos para 10x:**
1. **MongoDB:** activar sharding (`category.english + _id` para products, `{product_id: "hashed"}` para reviews >10M docs)
2. **PostgreSQL:** Transaction Pooler puerto 6543 + read replicas para queries analíticas
3. **Redis:** TTL catálogo 5min · precios 60s · sesiones 1h · `DECR` atómico de stock (Black Friday)
4. **CI/CD schemas:** Flyway/Liquibase para PG · Schema Versioning (`_schemaVersion`) + `$jsonSchema` para MongoDB

---

## Referencias

- Brewer, E. A. (2000). *Towards robust distributed systems*. PODC Keynote.
- Gilbert, S., & Lynch, N. (2002). Brewer's conjecture and the feasibility of consistent, available, partition-tolerant web services. *ACM SIGACT News, 33*(2), 51–59.
- Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly Media.
- Fowler, M. (2011). *NoSQL Distilled: A Brief Guide to the Emerging World of Polyglot Persistence*. Addison-Wesley.
- MongoDB, Inc. (2026). *Schema Design Patterns: Attribute, Extended Reference, Bucket*. MongoDB Documentation.
- PostgreSQL Global Development Group. (2026). *PostgreSQL 17 Documentation — GIN, GiST, BRIN Indexes*.
- Olist. (2018). *Brazilian E-Commerce Public Dataset by Olist*. Kaggle.
