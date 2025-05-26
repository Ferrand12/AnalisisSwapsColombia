# Bloque3.py — versión FINAL con guardado de figura
# -------------------------------------------------
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ---------- Rutas ----------
BASE         = Path(__file__).parent
SIM_RATES    = BASE / "sim_rates_bloque1.csv"
SPREAD_FILE  = BASE / "spread_maestro.xlsx"     # hoja “Spreads”
OUT_CSV      = BASE / "bloque3_resultados.csv"
FIG_DIR      = BASE / "figs_bloque3"
FIG_DIR.mkdir(exist_ok=True)

# ---------- Parámetros globales ----------
N        = 180                    # meses
SALDO0   = 100_000_000            # COP
r_disc   = 0.10                   # 10 % EA
r_disc_m = (1 + r_disc) ** (1/12) - 1

escenarios = ["Optimista", "Base", "Pesimista"]

# ---------- Lectura de insumos ----------
df_sim   = pd.read_csv(SIM_RATES, index_col="Mes")
spreads  = pd.read_excel(SPREAD_FILE, sheet_name="Spreads", index_col="Mes")
spr_dict = spreads.iloc[0].to_dict()           # {'spread_Optimista':0.015, …}

# ---------- Helper: cuota nivelada ----------
def pmt(rate: float, nper: int, pv: float) -> float:
    """Cuota nivelada mensual (igual criterio que Excel)."""
    if rate == 0:
        return pv / nper
    return rate * pv / (1 - (1 + rate) ** -nper)

# ---------- Helper: genera flujo mensual dado vector de tasas ----------
def flujo_cuotas(tasas: np.ndarray, saldo0: float) -> np.ndarray:
    """Devuelve array de 180 cuotas usando PMT con la tasa del mes y plazo remanente."""
    cuotas, saldo, rem = [], saldo0, len(tasas)
    for r in tasas:
        cuota = pmt(r, rem, saldo)
        cuotas.append(-cuota)                 # egreso = negativo
        interes = saldo * r
        amort   = cuota - interes
        saldo  -= amort
        rem    -= 1
    return np.array(cuotas)

# ---------- Bucle principal ----------
resultados = []

for esc in escenarios:
    spread      = spr_dict[f"spread_{esc}"]
    tasas_var   = df_sim[f"r_{esc}"].values
    tasas_swap  = tasas_var + spread

    cuotas_var  = flujo_cuotas(tasas_var,  SALDO0)
    cuotas_swap = flujo_cuotas(tasas_swap, SALDO0)

    t = np.arange(1, N + 1)
    PV_var  = (cuotas_var  / (1 + r_disc_m) ** t).sum()
    PV_swap = (cuotas_swap / (1 + r_disc_m) ** t).sum()

    ahorro_abs = PV_var - PV_swap
    ahorro_pct = ahorro_abs / (-PV_var)

    resultados.append({
        "Escenario"   : esc,
        "VPN_variable": PV_var,
        "VPN_swap"    : PV_swap,
        "Ahorro_swap" : ahorro_abs,
        "Ahorro_pct"  : ahorro_pct,
    })

df_out = (
    pd.DataFrame(resultados)
      .set_index("Escenario")
      .sort_index()
)

# ---------- Salida a consola y CSV ----------
print("\n----- BLOQUE 3 – RESULTADOS (COP) -----\n")
print(df_out[["VPN_variable", "VPN_swap", "Ahorro_swap"]]
      .applymap(lambda x: f"{x:,.0f}"))
print("\n% de ahorro:\n", (df_out["Ahorro_pct"] * 100).round(2).astype(str) + " %")

df_out.to_csv(OUT_CSV, float_format="%.4f")

# ---------- Gráfico ----------
fig, ax1 = plt.subplots(figsize=(8, 5))
x = np.arange(len(escenarios))
ax1.bar(x, df_out["Ahorro_swap"] / 1e6,
        color=["#2ca02c", "#1f77b4", "#d62728"])
ax1.set_ylabel("Ahorro vía swap (millones COP)")
ax1.set_xticks(x)
ax1.set_xticklabels(escenarios, fontsize=10)
ax1.set_title("Valor presente del ahorro cubriéndose con swap • Colombia")

ax2 = ax1.twinx()
ax2.plot(x, df_out["Ahorro_pct"] * 100, "k--o")
ax2.set_ylabel("Ahorro %")
for i, v in enumerate(df_out["Ahorro_pct"] * 100):
    ax2.text(i, v + 1, f"{v:.1f} %", ha="center")

fig.tight_layout()

# --- Guardado automático ---
fig_path = FIG_DIR / "ahorro_swap_bloque3.png"
plt.savefig(fig_path, dpi=120)
print(f"\n✅ Figura guardada en {fig_path.relative_to(BASE)}")

plt.show()