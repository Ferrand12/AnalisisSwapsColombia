# Bloque4.py – VaR del ahorro a 12 m para los tres escenarios
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ---------- rutas ----------
BASE = Path(__file__).parent
SIM_RATES_CSV = BASE / "sim_rates_bloque1.csv"
SPREADS_XLSX  = BASE / "spread_maestro.xlsx"       # hoja “Spreads”
OUT_CSV       = BASE / "bloque4_VaR.csv"
FIG_DIR       = BASE / "figs_bloque4"
FIG_DIR.mkdir(exist_ok=True)

# ---------- parámetros ----------
HORIZON    = 12     # meses
N_PATHS    = 10_000 # Monte Carlo
CONF       = 0.95
ALPHA      = 1 - CONF
SALDO0     = 100_000_000     # COP
r_desc_EA  = 0.10
r_desc_m   = (1+r_desc_EA)**(1/12) - 1

ESCENARIOS = ["Optimista", "Base", "Pesimista"]     # orden coherente

# ---------- helpers ----------
def pmt(rate, nper, pv):
    """Cuota nivelada (vectorizada)"""
    rate = np.asarray(rate, dtype=float)
    return np.where(rate==0, pv/nper, rate*pv/(1-(1+rate)**-nper))

def flujo_cuotas(tasas, saldo0):
    n = len(tasas)
    saldo = saldo0
    cuotas = np.empty(n)
    for k, r in enumerate(tasas):
        c = pmt(r, n-k, saldo)
        cuotas[k] = -c
        int_k = saldo*r
        amort = c - int_k
        saldo -= amort
    return cuotas

# ---------- leer insumos ----------
df_sim = pd.read_csv(SIM_RATES_CSV, index_col="Mes")
spread_row = (pd.read_excel(SPREADS_XLSX, sheet_name="Spreads",
                 index_col="Mes").iloc[0])
SPREADS = {esc: spread_row[f"spread_{esc}"] for esc in ESCENARIOS}

# ---------- loop escenarios ----------
results = []

for esc in ESCENARIOS:
    r_hist = df_sim[f"r_{esc}"].values[:HORIZON]

    # --- calibrar Vasicek ---
    y_t, y_tm1 = r_hist[1:], r_hist[:-1]
    beta   = np.polyfit(y_tm1, y_t, 1)[0]
    kappa  = -np.log(beta)
    mu     = np.mean(r_hist)
    sigma  = np.std(y_t - beta*y_tm1) * np.sqrt(2*kappa/(1-beta**2))

    # --- simular ---
    rng = np.random.default_rng(42)
    r0  = r_hist[-1]
    sim_r = np.empty((N_PATHS, HORIZON))
    for p in range(N_PATHS):
        r = r0
        for t in range(HORIZON):
            r += kappa*(mu-r) + sigma*rng.standard_normal()
            sim_r[p,t] = max(r, 0)

    # --- ahorro por trayectoria ---
    spr = SPREADS[esc]
    tiempos = np.arange(1, HORIZON+1)

    ahorros = np.empty(N_PATHS)
    for i in range(N_PATHS):
        r_var  = sim_r[i]
        r_fix  = r_var + spr
        cu_var = flujo_cuotas(r_var, SALDO0)[:HORIZON]
        cu_fix = flujo_cuotas(r_fix, SALDO0)[:HORIZON]
        pv_var = (cu_var/(1+r_desc_m)**tiempos).sum()
        pv_fix = (cu_fix/(1+r_desc_m)**tiempos).sum()
        ahorros[i] = pv_var - pv_fix

    VaR_abs = np.percentile(ahorros, ALPHA*100)
    VaR_pct = VaR_abs/ahorros.mean()

    results.append({"Escenario": esc,
                    "Ahorro_med": ahorros.mean(),
                    "VaR_abs":    VaR_abs,
                    "VaR_pct":    VaR_pct})

    # --- histograma individual ---
    plt.figure(figsize=(7,4))
    plt.hist(ahorros/1e6, bins=60, color="#1f77b4", alpha=.75)
    plt.axvline(VaR_abs/1e6, color="red", lw=2,
                label=f"VaR 95 % = {VaR_abs/1e6:,.1f} MM")
    plt.title(f"Distribución del ahorro (12 m) • {esc}")
    plt.xlabel("Ahorro vía swap (MM COP)")
    plt.ylabel("Frecuencia")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / f"hist_{esc}.png", dpi=120)
    plt.close()

# ---------- tabla y CSV ----------
df_res = (pd.DataFrame(results)
            .set_index("Escenario")
            .assign(Ahorro_med=lambda d: d.Ahorro_med.round(0),
                    VaR_abs    =lambda d: d.VaR_abs.round(0),
                    VaR_pct    =lambda d: (d.VaR_pct*100).round(2)))
df_res.to_csv(OUT_CSV)
print("\n------ BLOQUE 4 – VaR 95 % (12 m) ------")
print(df_res.to_string())

# ---------- comparación gráfica ----------
colores = ["#2ca02c","#1f77b4","#d62728"]
plt.figure(figsize=(6,4))
bars = plt.bar(df_res.index, df_res["VaR_abs"]/1e6,
               color=colores, alpha=.8)
plt.ylabel("VaR 95 % (millones COP)")
plt.title("VaR 95 % del ahorro anual por escenario")

for bar,val in zip(bars, df_res["VaR_abs"]/1e6):
    plt.text(bar.get_x()+bar.get_width()/2, val+0.2,
             f"{val:,.1f}", ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(FIG_DIR / "VaR_comparativo.png", dpi=120)
plt.show()