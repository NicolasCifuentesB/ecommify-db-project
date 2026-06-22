# Ecommify — Arquitectura Híbrida de Base de Datos

**Grupo E25 | Diseño y Optimización de Bases de Datos — MAS 2026-3 G1G2**  
Maestría en Arquitectura de Software · Universidad de La Sabana  
Docente: Miguel Alfonso Varela · 2026

**Integrantes:** Andres Camilo Meneses Ortega · David Hernando Monsalve Delima · Eduardo Trujillo Santos · Nicolás Cifuentes Barriga

---

## Descripción del Proyecto

Ecommify es una plataforma de e-commerce que implementa una **arquitectura híbrida de persistencia políglota**: PostgreSQL gestiona el núcleo transaccional (pedidos, pagos, clientes) y MongoDB Atlas gestiona el catálogo de productos y la analítica de reseñas.

El proyecto aplica el dataset real de Olist Brazilian E-Commerce (99,441 pedidos · 112,650 ítems · 1,000 productos MongoDB · 3,118 reseñas) sobre infraestructura cloud gratuita (Supabase + Atlas M0).

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                      ECOMMIFY PLATFORM                       │
├───────────────────────────┬─────────────────────────────────┤
│   PostgreSQL (Supabase)   │       MongoDB Atlas (M0)         │
│   [CP — Consistencia]     │       [AP — Disponibilidad]      │
├───────────────────────────┼─────────────────────────────────┤
│ • customers   (99,441)    │ • products        (1,000 docs)   │
│ • orders      (99,441)    │ • reviews         (3,118 docs)   │
│ • order_items (112,650)   │ • reviews_buckets (  954 docs)   │
│ • payments    (103,877)   │                                  │
│ • sellers       (3,095)   │  Patrones: ESR · Bucket ·        │
│ • geolocations (19,015)   │  Attribute · Extended Reference  │
│                           │                                  │
│ Features: GENERATED cols, │  Features: $match temprano,      │
│ GIN/GiST/BRIN indexes,    │  Atlas Search, sharding          │
│ particionamiento RANGE,   │  key: category.english + _id     │
│ pg_trgm, PostGIS          │                                  │
└───────────────────────────┴─────────────────────────────────┘
```

### Decisión de partición PostgreSQL vs MongoDB

| Módulo | Base de Datos | Razón |
|--------|--------------|-------|
| Orders / Pagos | PostgreSQL | ACID crítico, FK con customers |
| Customers | PostgreSQL | Integridad referencial, search_vector GENERATED |
| Catálogo de productos | MongoDB | Specs variables por categoría (Attribute Pattern) |
| Reseñas individuales | MongoDB | Alta tasa de escritura, consistencia eventual aceptable |
| Analítica temporal | MongoDB | Bucket Pattern: 3,118 → 954 docs (-69.4%) |

---

## Resultados Clave de Rendimiento

| Operación | Antes | Después | Mejora |
|-----------|-------|---------|--------|
| MongoDB Q1 catálogo (ESR) | 1,000 docsExamined | 328 | **-67.2%** |
| MongoDB Attribute Pattern | 1,000 docsExamined | 8 | **-99.2%** |
| MongoDB Bucket Pattern | 3,118 documentos | 954 | **-69.4%** |
| PostgreSQL Q4 pedidos pendientes | 13.85 ms | 1.01 ms | **-92.7%** |
| PostgreSQL Q7 entregas por estado | 378.03 ms | 91.68 ms | **+75.7%** |
| PostgreSQL Q2 partition pruning | 1,180 ms | 21.75 ms | **-98.2%** |

---

## Estructura del Repositorio

```
ecommify-db-project/
├── postgresql/
│   └── schema/
│       ├── schema.psql          # DDL principal (tablas, constraints, tipos)
│       ├── tables.psql          # Definición detallada de tablas
│       ├── extensions.psql      # pg_trgm, PostGIS, uuid-ossp
│       ├── index.psql           # Índices B-tree, GIN, GiST, BRIN, parciales
│       ├── partitions.psql      # Particionamiento RANGE por purchase_timestamp
│       └── triggers.psql        # Triggers para updated_at, search_vector
│   └── queries/
│       └── fill_tables.psql     # Carga inicial del dataset Olist
│   └── seed_data/               # CSVs del dataset Olist Brazilian E-Commerce
│       ├── olist_orders_dataset.csv
│       ├── olist_customers_dataset.csv
│       ├── olist_order_items_dataset.csv
│       ├── olist_order_payments_dataset.csv
│       ├── olist_products_dataset.csv
│       ├── olist_sellers_dataset.csv
│       ├── olist_geolocation_dataset.csv
│       └── product_category_name_translation.csv
├── mongodb/
│   └── schema/
│       ├── create.py            # Creación de colecciones con $jsonSchema
│       ├── products.py          # Modelado de productos (Attribute + Extended Ref)
│       ├── reviews.py           # Reseñas individuales con validación
│       ├── carts.py             # Carritos (TTL index)
│       ├── analytics.py         # Colección de analítica
│       ├── recommendations.py   # Motor de recomendaciones
│       ├── product_views.py     # Registro de vistas de producto
│       ├── analytic_pipeline.py # Pipeline de aggregation (7 stages)
│       ├── index.py             # Creación de índices ESR y especializados
│       └── validation.py        # $jsonSchema validation rules
├── notebooks/
│   ├── U1 - Analisis exploratorio.ipynb      # EDA del dataset Olist
│   ├── U2 - Tipos Avanzados.ipynb            # PostgreSQL tipos avanzados
│   ├── U3 - MongoDB Ecommify.ipynb           # Modelado MongoDB
│   ├── U4 - Optimizacion Implementacion.ipynb # Índices y particionamiento PG
│   └── U5 - Optimizacion MongoDB.ipynb       # ESR, Bucket, Atlas Search
├── docs/
│   └── [PDFs de entregas anteriores]
└── README.md
```

---

## Reproducción del Entorno

### Requisitos

- Python 3.10+
- PostgreSQL 15+ (o cuenta Supabase gratuita)
- MongoDB Atlas M0 (cuenta gratuita)
- Jupyter Notebook / Google Colab

### Setup PostgreSQL (Supabase)

```bash
pip install psycopg2-binary pandas matplotlib seaborn

# Ejecutar DDL en orden:
psql $DATABASE_URL -f postgresql/schema/extensions.psql
psql $DATABASE_URL -f postgresql/schema/schema.psql
psql $DATABASE_URL -f postgresql/schema/tables.psql
psql $DATABASE_URL -f postgresql/schema/triggers.psql
psql $DATABASE_URL -f postgresql/schema/index.psql
psql $DATABASE_URL -f postgresql/schema/partitions.psql

# Cargar datos Olist:
psql $DATABASE_URL -f postgresql/queries/fill_tables.psql
```

Variables de entorno requeridas:
```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/postgres
```

### Setup MongoDB (Atlas)

```bash
pip install pymongo pandas matplotlib seaborn tabulate

# Crear colecciones y esquemas:
python mongodb/schema/create.py
python mongodb/schema/products.py
python mongodb/schema/reviews.py
python mongodb/schema/index.py
```

Variable de entorno requerida:
```
MONGO_URI=mongodb+srv://USER:PASSWORD@clustermaestriadb.qibjniy.mongodb.net/
```

### Ejecutar notebooks

```bash
# Instalar dependencias
pip install jupyter psycopg2-binary pymongo pandas matplotlib seaborn tabulate

# Abrir en Jupyter o subir a Google Colab
jupyter notebook notebooks/
```

Los notebooks están numerados en orden de ejecución (U1 → U5).

---

## Teorema CAP — Clasificación por Módulo

| Módulo | BD | Garantías | Configuración |
|--------|-----|-----------|---------------|
| Orders / Pagos | PostgreSQL | **CP** | `synchronous_commit=on`, `SERIALIZABLE` |
| Order Items | PostgreSQL | **CP** | FK con orders, GENERATED total_amount |
| Customers | PostgreSQL | **CP** | search_vector GENERATED, FK con orders |
| Catálogo (products) | MongoDB | **AP** | `readPreference=secondaryPreferred`, lag 1-5s aceptable |
| Reseñas (reviews) | MongoDB | **AP** | `writeConcern={w:1, j:false}`, throughput > consistencia |
| Buckets analíticos | MongoDB | **AP** | Reconstrucción periódica via `$out` pipeline |

---

## Índices Implementados

### PostgreSQL

| Índice | Tipo | Tabla | Impacto |
|--------|------|-------|---------|
| `idx_orders_status` | B-tree | orders | Filtros por estado |
| `idx_orders_status_ts` | B-tree compuesto | orders | Q1/Q2: elimina Sort explícito |
| `idx_orders_active_partial` | Parcial | orders | Q4: -92.7% latencia (solo 0.3% de filas) |
| `idx_orders_purchase_brin` | BRIN | orders | 100x más compacto que B-tree; queries de rango |
| `idx_items_seller_price` | B-tree compuesto | order_items | Q6: Index Only Scan posible |
| `idx_orders_shipping_gin` | GIN | orders | Búsqueda JSONB en shipping_address |

### MongoDB

| Índice | Tipo | Colección | Impacto |
|--------|------|-----------|---------|
| `idx_esr_active_rating_price` | ESR compuesto | products | 1,000 → 328 docsExamined (-67.2%) |
| `idx_esr_active_category_sold` | ESR compuesto | products | Catálogo por categoría + ventas |
| `idx_attribute_pattern_specs` | Compuesto array | products | 1,000 → 8 docsExamined (-99.2%) |
| `idx_partial_active_high_rating` | Parcial | products | Solo activos con rating ≥ 4.0 |
| `idx_text_products` | Text (Atlas Search) | products | Full-text ponderado (name×10, tags×5) |
| `idx_bucket_product_month` | Compuesto | reviews_buckets | Analítica temporal O(1) por período |

---

## Tecnologías

| Capa | Tecnología | Versión | Uso |
|------|-----------|---------|-----|
| BD Relacional | PostgreSQL | 17.6 | Core transaccional + analítica estructurada |
| BD Documental | MongoDB Atlas | 7.0 | Catálogo flexible + analítica de reviews |
| Infraestructura PG | Supabase | Free tier | Hosting + pgBouncer + REST API |
| Infraestructura MDB | Atlas M0 | Free tier | Cluster multi-región + Performance Advisor |
| Lenguaje análisis | Python 3.12 | 3.12 | Notebooks, ETL, benchmarks |
| Visualización | Matplotlib / Seaborn | latest | Gráficas de rendimiento |
| Dataset | Olist Brazilian E-Commerce | 2018 | Kaggle — datos reales de producción |

---

## Recomendaciones de Escalamiento (10x)

Para escalar de Free Tier a 10x carga productiva:

1. **MongoDB**: Migrar a Atlas M10 (dedicado) + activar sharding con `category.english + _id`
2. **PostgreSQL**: Activar pgBouncer (ya incluido en Supabase Pro) + read replicas
3. **Caché**: Redis para catálogo (reduce carga Atlas ~70% en reads) y sesiones de usuario
4. **Búsqueda**: Atlas Search dedicado (ya implementado en U5, activar en M10+)
5. **Streaming**: Apache Kafka para desacoplar ingesta de reviews del pipeline de buckets
6. **CI/CD**: Flyway para migraciones PG + Schema Versioning (`_schemaVersion`) para MongoDB

---

## Referencias

- Brewer, E. A. (2000). Towards robust distributed systems. *PODC Keynote*.
- Gilbert, S., & Lynch, N. (2002). Brewer's conjecture and the feasibility of consistent, available, partition-tolerant web services. *ACM SIGACT News, 33*(2), 51-59.
- Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly Media.
- Fowler, M. (2011). *NoSQL Distilled*. Addison-Wesley.
- MongoDB, Inc. (2026). Schema Design Patterns. MongoDB Documentation.
- PostgreSQL Global Development Group. (2026). PostgreSQL 17 Documentation.
- Olist. (2018). *Brazilian E-Commerce Public Dataset*. Kaggle.
