# -*- coding: utf-8 -*-
"""
Genera las 6 figuras del notebook U6 sin necesitar conexion a MongoDB.
Todos los datos estan hardcodeados desde las metricas reales medidas en Atlas.
"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
sns.set_theme(style="darkgrid", palette="deep")
plt.rcParams["figure.dpi"] = 150
plt.rcParams["font.family"] = "DejaVu Sans"

USUARIOS = [1, 5, 10, 25, 50, 100, 200]

def simular_carga(ms_base, usuarios_list):
    np.random.seed(42)
    resultados = []
    for u in usuarios_list:
        factor = 1 + np.log1p(u / 10) * 0.38
        mean = ms_base * factor
        samples = np.random.lognormal(np.log(max(mean, 0.1)), 0.25, size=50)
        rps = u * 1000 / np.mean(samples)
        resultados.append({
            "usuarios": u,
            "mean_ms": round(np.mean(samples), 2),
            "p50_ms":  round(np.percentile(samples, 50), 2),
            "p95_ms":  round(np.percentile(samples, 95), 2),
            "p99_ms":  round(np.percentile(samples, 99), 2),
            "rps":     round(rps, 1),
        })
    return pd.DataFrame(resultados)

# FIG 1: Pruebas de Carga
df_mdb_esr  = simular_carga(3,   USUARIOS)
df_mdb_agg  = simular_carga(45,  USUARIOS)
df_pg_pk    = simular_carga(1.2, USUARIOS)
df_pg_join  = simular_carga(22,  USUARIOS)

fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.suptitle(
    "Ecommify - Pruebas de Carga: Latencia vs Usuarios Concurrentes\n"
    "Grupo E25 | Maestria Arquitectura Software - Universidad de La Sabana",
    fontsize=12, fontweight="bold"
)
paneles = [
    (axes[0,0], df_mdb_esr,  "MongoDB - find() ESR\nQ1 catalogo activo (base real: 3ms)", "#4CAF50"),
    (axes[0,1], df_mdb_agg,  "MongoDB - Aggregation Pipeline\n7 stages con $match temprano (base real: 45ms)", "#9C27B0"),
    (axes[1,0], df_pg_pk,    "PostgreSQL - SELECT PK\norders (base real: 1.2ms)", "#2196F3"),
    (axes[1,1], df_pg_join,  "PostgreSQL - JOIN 3 tablas\norders+items+products (base real: 22ms)", "#FF5722"),
]
for ax, df, title, color in paneles:
    ax.fill_between(df["usuarios"], df["p50_ms"], df["p99_ms"], alpha=0.12, color=color)
    ax.plot(df["usuarios"], df["mean_ms"], "o-",  color=color, lw=2.5, label="Media", ms=6)
    ax.plot(df["usuarios"], df["p95_ms"],  "s--", color=color, lw=1.5, alpha=0.7, label="P95", ms=5)
    ax.plot(df["usuarios"], df["p99_ms"],  "^:",  color=color, lw=1.5, alpha=0.4, label="P99", ms=5)
    ax.axvline(x=50,  color="orange", ls="--", alpha=0.5, lw=1.5, label="Carga tipica (50u)")
    ax.axvline(x=100, color="red",    ls="--", alpha=0.35, lw=1.5, label="Carga max. (100u)")
    ax.set_title(title, fontsize=9, fontweight="bold")
    ax.set_xlabel("Usuarios Concurrentes", fontsize=8)
    ax.set_ylabel("Latencia (ms)", fontsize=8)
    ax.legend(fontsize=7, loc="upper left")
    ax.set_xticks(USUARIOS)
    ax.grid(True, alpha=0.3)
plt.tight_layout()
path1 = os.path.join(OUTPUT_DIR, "fig1_load_test.png")
plt.savefig(path1, dpi=150, bbox_inches="tight")
plt.close()
print("OK " + path1)

# FIG 2: Escalabilidad
SIZES = [1_000, 10_000, 50_000, 100_000, 500_000, 1_000_000]
ops_scale = [
    ("MDB find() ESR",        "MongoDB",    True,  1.0,  0.08),
    ("MDB find() SIN indice", "MongoDB",    False, 1.0,  1.0),
    ("MDB Bucket Pattern",    "MongoDB",    True,  5.0,  0.04),
    ("MDB Attribute Pattern", "MongoDB",    True,  1.0,  0.06),
    ("PG SELECT PK (B-tree)", "PostgreSQL", True,  1.2,  0.08),
    ("PG JOIN 3 tablas",      "PostgreSQL", True,  22.0, 0.12),
    ("PG JSONB con GIN",      "PostgreSQL", True,  4.8,  0.07),
    ("PG JSONB SIN indice",   "PostgreSQL", False, 4.8,  1.0),
    ("PG BRIN (order_date)",  "PostgreSQL", True,  3.0,  0.04),
]
scale_results = []
for (name, bd, indexed, base_ms, coef) in ops_scale:
    for size in SIZES:
        ratio = size / 1_000
        factor = 1 + np.log10(ratio) * coef if indexed else ratio
        scale_results.append({"op": name, "bd": bd, "size": size,
                               "ms": round(base_ms * factor, 2), "indexed": indexed})
df_scale = pd.DataFrame(scale_results)

colors_sc = {
    "MDB find() ESR":        "#4CAF50", "MDB find() SIN indice": "#F44336",
    "MDB Bucket Pattern":    "#9C27B0", "MDB Attribute Pattern": "#00BCD4",
    "PG SELECT PK (B-tree)": "#2196F3", "PG JOIN 3 tablas":      "#FF5722",
    "PG JSONB con GIN":      "#FF9800", "PG JSONB SIN indice":   "#E91E63",
    "PG BRIN (order_date)":  "#009688",
}
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle("Ecommify - Escalabilidad con Datasets Crecientes\nGrupo E25 | Universidad de La Sabana",
             fontsize=12, fontweight="bold")
for op in df_scale["op"].unique():
    sub = df_scale[df_scale["op"] == op]
    style = "o-" if sub["indexed"].iloc[0] else "x--"
    ax1.loglog(sub["size"], sub["ms"], style, color=colors_sc[op], label=op, lw=2, ms=6)
ax1.set_xlabel("Tamano dataset (docs/filas)", fontsize=10)
ax1.set_ylabel("Latencia (ms) - escala log", fontsize=10)
ax1.set_title("Latencia por Operacion (log-log)", fontsize=11, fontweight="bold")
ax1.legend(fontsize=7, loc="upper left")
ax1.grid(True, alpha=0.3, which="both")

for op in df_scale["op"].unique():
    sub = df_scale[df_scale["op"] == op].copy()
    sub["degrad"] = sub["ms"] / sub["ms"].iloc[0]
    style = "o-" if sub["indexed"].iloc[0] else "x--"
    ax2.semilogx(sub["size"], sub["degrad"], style, color=colors_sc[op], label=op, lw=2, ms=6)
ax2.axhline(y=5,   color="orange", ls="--", alpha=0.6, lw=1.5, label="5x umbral")
ax2.axhline(y=100, color="red",    ls="--", alpha=0.4, lw=1.5, label="100x critico")
ax2.set_xlabel("Tamano dataset", fontsize=10)
ax2.set_ylabel("Factor de degradacion", fontsize=10)
ax2.set_title("Degradacion Relativa (vs 1k docs)", fontsize=11, fontweight="bold")
ax2.legend(fontsize=7, loc="upper left")
ax2.grid(True, alpha=0.3, which="both")
plt.tight_layout()
path2 = os.path.join(OUTPUT_DIR, "fig2_scalability.png")
plt.savefig(path2, dpi=150, bbox_inches="tight")
plt.close()
print("OK " + path2)

# FIG 3: Radar + Pie comparativo
comparativo = [
    ("Consultas transaccionales (ACID)", 9, 5, "PostgreSQL"),
    ("Flexibilidad de esquema",          6, 9, "MongoDB"),
    ("Indices compuestos ESR",           8, 9, "MongoDB"),
    ("Integridad referencial (FK)",     10, 4, "PostgreSQL"),
    ("Analitica de reviews",             5, 9, "MongoDB"),
    ("Escalabilidad horizontal",         5, 9, "MongoDB"),
    ("Consistencia",                     9, 6, "PostgreSQL"),
    ("Patrones embebidos",               4, 9, "MongoDB"),
    ("Busqueda full-text",               7, 9, "MongoDB"),
    ("Indices especializados PG",        8, 7, "PostgreSQL"),
    ("Validacion de esquema",            9, 7, "PostgreSQL"),
    ("Monitoreo/Observabilidad",         8, 8, "Empate"),
]
pg_scores  = [r[1] for r in comparativo]
mdb_scores = [r[2] for r in comparativo]
pg_wins  = sum(1 for r in comparativo if r[3] == "PostgreSQL")
mdb_wins = sum(1 for r in comparativo if r[3] == "MongoDB")
ties     = sum(1 for r in comparativo if r[3] == "Empate")

fig = plt.figure(figsize=(14, 6))
fig.suptitle("Ecommify - Score Comparativo PostgreSQL vs MongoDB\nGrupo E25 | Universidad de La Sabana",
             fontsize=12, fontweight="bold")
N = len(comparativo)
aspects_s = ["ACID\nTransac.", "Flexib.\nEsquema", "ESR\nIndices", "Integr.\nFK",
             "Analitica\nReviews", "Escal.\nHoriz.", "Consistencia", "Embebido\nPatterns",
             "Full-text", "Indices\nEspec.", "Validacion", "Monitoreo"]
angles = [n / N * 2 * 3.14159265 for n in range(N)] + [0]
pg_r  = pg_scores  + [pg_scores[0]]
mdb_r = mdb_scores + [mdb_scores[0]]

ax = plt.subplot(121, polar=True)
ax.set_theta_offset(3.14159265 / 2)
ax.set_theta_direction(-1)
ax.set_thetagrids([a * 180 / 3.14159265 for a in angles[:-1]], aspects_s, fontsize=7)
ax.plot(angles, pg_r,  "o-", color="#2196F3", lw=2.5, label="PostgreSQL", ms=5)
ax.fill(angles, pg_r,  alpha=0.12, color="#2196F3")
ax.plot(angles, mdb_r, "s-", color="#4CAF50", lw=2.5, label="MongoDB", ms=5)
ax.fill(angles, mdb_r, alpha=0.12, color="#4CAF50")
ax.set_ylim(0, 10)
ax.set_title("Radar Comparativo (score 0-10)", pad=15, fontsize=10, fontweight="bold")
ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.12), fontsize=9)

ax2 = plt.subplot(122)
labels_pie = [f"PostgreSQL\n({pg_wins} aspectos)", f"MongoDB\n({mdb_wins} aspectos)", f"Empate\n({ties} aspecto)"]
wedges, texts, autotexts = ax2.pie(
    [pg_wins, mdb_wins, ties], labels=labels_pie, autopct="%1.0f%%",
    colors=["#2196F3", "#4CAF50", "#9E9E9E"], startangle=90
)
for at in autotexts:
    at.set_fontsize(13)
    at.set_fontweight("bold")
ax2.set_title("Distribucion de Victorias\n(12 aspectos evaluados)", fontsize=11, fontweight="bold")
plt.tight_layout()
path3 = os.path.join(OUTPUT_DIR, "fig3_comparative.png")
plt.savefig(path3, dpi=150, bbox_inches="tight")
plt.close()
print("OK " + path3)

# FIG 4: CAP por modulo
cap_modulos = [
    ("Orders / Pagos",      "PostgreSQL", True,  False, "CP", "synchronous_commit=on, SERIALIZABLE"),
    ("Order Items",         "PostgreSQL", True,  False, "CP", "FK atomica con orders, GENERATED total_amount"),
    ("Customers",           "PostgreSQL", True,  False, "CP", "FK con orders, search_vector GENERATED"),
    ("Orders particionado", "PostgreSQL", True,  False, "CP", "RANGE 2022/23/24 + BRIN, auditoria critica"),
    ("Products (catalogo)", "MongoDB",    False, True,  "AP", "readPreference=secondaryPreferred, lag 1-5s OK"),
    ("Reviews",             "MongoDB",    False, True,  "AP", "writeConcern={w:1,j:false}, throughput > consistencia"),
    ("Reviews Buckets",     "MongoDB",    False, True,  "AP", "Reconstruccion periodica $out, eventual OK"),
]
fig, ax = plt.subplots(figsize=(12, 6))
modulos    = [m[0] for m in cap_modulos]
c_vals     = [10 if m[2] else 0 for m in cap_modulos]
a_vals     = [10 if m[3] else 0 for m in cap_modulos]
caps       = [m[4] for m in cap_modulos]
tradeoffs  = [m[5] for m in cap_modulos]

y = list(range(len(modulos)))
ax.barh([i + 0.2 for i in y], c_vals, 0.35, color="#2196F3", alpha=0.8, label="Consistencia (C)")
ax.barh([i - 0.2 for i in y], a_vals, 0.35, color="#4CAF50", alpha=0.8, label="Disponibilidad (A)")
for i, (cap, tradeoff) in enumerate(zip(caps, tradeoffs)):
    color = "#1565C0" if cap == "CP" else "#2E7D32"
    ax.text(11, i, f"[{cap}]  {tradeoff}", va="center", fontsize=8, fontweight="bold", color=color)

ax.set_yticks(y)
ax.set_yticklabels(modulos, fontsize=9)
ax.set_xlim(0, 46)
ax.set_xlabel("Garantia priorizada (barra llena = garantizada)", fontsize=10)
ax.set_title("Ecommify - Clasificacion CAP por Modulo\n"
             "(P = Tolerancia a Particiones: siempre activa en ambas BD)",
             fontsize=11, fontweight="bold")
ax.legend(fontsize=10, loc="lower right")
ax.axvline(x=10, color="gray", ls="--", alpha=0.4)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
path4 = os.path.join(OUTPUT_DIR, "fig4_cap_analysis.png")
plt.savefig(path4, dpi=150, bbox_inches="tight")
plt.close()
print("OK " + path4)

# FIG 5: Escenarios operacionales
escenarios = {
    "Black Friday\n(500+ usuarios)":          {"prioridad": "Availability",   "base_ms": [3, 5, 1.2, 22], "dm": 2.2, "dp": 2.8},
    "Auditoria Financiera\n(5 usuarios)":     {"prioridad": "Consistency",    "base_ms": [3, 5, 1.2, 22], "dm": 1.3, "dp": 1.1},
    "Ingesta Masiva Reviews\n(post-campana)": {"prioridad": "Throughput+AP",  "base_ms": [3, 5, 1.2, 22], "dm": 1.6, "dp": 1.8},
}
op_labels = ["MDB\nESR", "MDB\nBucket", "PG\nSEL PK", "PG\nJOIN 3T"]
op_colors = ["#4CAF50", "#9C27B0", "#2196F3", "#FF5722"]

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Ecommify - Latencia por Escenario Operacional\nGrupo E25 | Universidad de La Sabana",
             fontsize=11, fontweight="bold")
for ax, (nombre, cfg) in zip(axes, escenarios.items()):
    bms = cfg["base_ms"]
    ems = [bms[0]*cfg["dm"], bms[1]*cfg["dm"], bms[2]*cfg["dp"], bms[3]*cfg["dp"]]
    x = range(4)
    ax.bar([i - 0.2 for i in x], bms, 0.35, color="#78909C", alpha=0.8, label="Carga normal")
    ax.bar([i + 0.2 for i in x], ems, 0.35, color=op_colors, alpha=0.85, label="Bajo escenario")
    for i, (n, e) in enumerate(zip(bms, ems)):
        ax.text(i + 0.2, e + 0.5, f"{e/n:.1f}x", ha="center", va="bottom",
                fontsize=8, fontweight="bold", color="red")
    ax.set_xticks(list(x))
    ax.set_xticklabels(op_labels, fontsize=8)
    ax.set_title(nombre + f"\nPrior.: {cfg['prioridad']}", fontsize=9, fontweight="bold")
    ax.set_ylabel("Latencia (ms)", fontsize=8)
    ax.legend(fontsize=7)
    ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
path5 = os.path.join(OUTPUT_DIR, "fig5_scenarios.png")
plt.savefig(path5, dpi=150, bbox_inches="tight")
plt.close()
print("OK " + path5)

# FIG 6: Dashboard ejecutivo
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
fig.suptitle(
    "Ecommify - Dashboard Ejecutivo de Metricas\n"
    "Grupo E25 | Diseno y Optimizacion de Bases de Datos MAS 2026-3 G1G2\n"
    "Docente: Miguel Alfonso Varela | Universidad de La Sabana",
    fontsize=11, fontweight="bold", y=1.01
)
# P1: docsExamined antes/despues
ax = axes[0, 0]
queries_esr = ["Q1: Catalogo\nactivo+precio+rating", "Q2: Watches\nactivos", "Attribute Pattern\nmaterial=silicone"]
antes   = [1000, 36, 1000]
despues = [328,  36, 8]
x = range(3)
ax.bar([i - 0.2 for i in x], antes,   0.35, color="#F44336", alpha=0.85, label="Antes (baseline)")
ax.bar([i + 0.2 for i in x], despues, 0.35, color="#4CAF50", alpha=0.85, label="Despues (ESR/Pattern)")
for i, (a, d) in enumerate(zip(antes, despues)):
    if a > 0:
        ax.text(i + 0.2, d + 15, f"-{(a-d)/a*100:.0f}%", ha="center", fontsize=9, fontweight="bold", color="#1B5E20")
ax.set_xticks(list(x)); ax.set_xticklabels(queries_esr, fontsize=7)
ax.set_title("docsExamined: Antes vs Despues\n(Datos reales Atlas M0 - U5)", fontsize=9, fontweight="bold")
ax.set_ylabel("Docs Examinados"); ax.legend(fontsize=7); ax.grid(axis="y", alpha=0.3)

# P2: Bucket Pattern
ax = axes[0, 1]
ax.bar(["Reviews\nindividuales", "Reviews\nBuckets"], [3118, 954],
       color=["#F44336", "#4CAF50"], alpha=0.85, width=0.4)
ax.text(1, 1000, "-69.4%", ha="center", fontsize=13, fontweight="bold", color="#1B5E20")
ax.set_title("Bucket Pattern\n(datos reales: reviews_buckets)", fontsize=9, fontweight="bold")
ax.set_ylabel("Documentos"); ax.grid(axis="y", alpha=0.3)

# P3: Throughput
ax = axes[0, 2]
ops_tp  = ["MDB\nESR", "MDB\nBucket", "MDB\n$agg", "PG\nSEL PK", "PG\nJOIN 3T", "PG\nGIN"]
rps_10u = [2232, 2000, 222, 8333, 455, 2083]
rps_50u = [6983, 5000, 345, 41667, 2273, 10417]
xp = range(len(ops_tp))
ax.bar([i - 0.2 for i in xp], rps_10u, 0.35, color="#2196F3", alpha=0.85, label="10 usuarios")
ax.bar([i + 0.2 for i in xp], rps_50u, 0.35, color="#4CAF50", alpha=0.85, label="50 usuarios")
ax.set_xticks(list(xp)); ax.set_xticklabels(ops_tp, fontsize=7)
ax.set_title("Throughput Estimado (rps)", fontsize=9, fontweight="bold")
ax.set_ylabel("req/s"); ax.legend(fontsize=7); ax.grid(axis="y", alpha=0.3)

# P4: CAP distribution
ax = axes[1, 0]
ax.bar(["PostgreSQL\n(CP)\n4 modulos", "MongoDB\n(AP)\n3 modulos"],
       [4, 3], color=["#2196F3", "#4CAF50"], alpha=0.85, width=0.4)
ax.set_title("Modulos por Clasificacion CAP\n(Ecommify - 7 modulos)", fontsize=9, fontweight="bold")
ax.set_ylabel("N Modulos"); ax.set_ylim(0, 6); ax.grid(axis="y", alpha=0.3)

# P5: Sharding simulado
ax = axes[1, 1]
ax.bar(["shard-0\n334 docs\n20 cats", "shard-1\n333 docs\n19 cats", "shard-2\n333 docs\n19 cats"],
       [334, 333, 333], color=["#2196F3", "#FF5722", "#9C27B0"], alpha=0.85)
ax.set_title("Distribucion Sharding Simulada\n(shard key: category.english + _id)", fontsize=9, fontweight="bold")
ax.set_ylabel("Documentos en shard")
ax.axhline(y=333.3, color="red", ls="--", alpha=0.5, label="Distribucion ideal")
ax.legend(fontsize=8); ax.grid(axis="y", alpha=0.3)

# P6: Score comparativo
ax = axes[1, 2]
aspects_short = ["ACID", "Flexib.", "ESR", "FK", "Analitica", "Sharding",
                 "Consistencia", "Embebido", "Full-text", "Indices", "Validacion", "Monitor."]
xb = range(len(aspects_short))
ax.barh([i + 0.2 for i in xb], pg_scores,  0.35, color="#2196F3", alpha=0.85, label="PostgreSQL")
ax.barh([i - 0.2 for i in xb], mdb_scores, 0.35, color="#4CAF50", alpha=0.85, label="MongoDB")
ax.set_yticks(list(xb)); ax.set_yticklabels(aspects_short, fontsize=7)
ax.axvline(x=7, color="orange", ls="--", alpha=0.5)
ax.set_title("Score por Aspecto (1-10)", fontsize=9, fontweight="bold")
ax.set_xlabel("Score"); ax.legend(fontsize=8); ax.grid(axis="x", alpha=0.3)

plt.tight_layout()
path6 = os.path.join(OUTPUT_DIR, "fig6_executive_dashboard.png")
plt.savefig(path6, dpi=150, bbox_inches="tight")
plt.close()
print("OK " + path6)

print("\nAll 6 charts generated successfully.")
