# Bloque2_v3.py  ----------------------------------------------------------
import pandas as pd
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt
from pathlib import Path
#  carpeta donde se guardarán todas las figuras de este bloque
FIG_DIR = Path(__file__).with_name("figs_bloque2")
FIG_DIR.mkdir(exist_ok=True)

ESC = ("Optimista", "Base", "Pesimista")

# ---------------------------------------------------------------- 1)  Spreads de “spread_maestro.xlsx”
spread_df = pd.read_excel("spread_maestro.xlsx", sheet_name="Spreads")
SPREAD_SWAP = {c.split("_", 1)[1].capitalize(): spread_df.at[0, c]
               for c in spread_df.columns if c.startswith("spread_")}

# ---------------------------------------------------------------- 2)  Trayectorias de tasas simuladas (Bloque 1)
rates = pd.read_csv("sim_rates_bloque1.csv")

# ---------------------------------------------------------------- 3)  Parámetros del crédito
MONTO        = 100_000_000      # COP
N_MESES      = 180
TASA_FIJA_EA = 0.13             # “tarifa de lista” 13 % EA
r_fija_m     = (1 + TASA_FIJA_EA) ** (1/12) - 1

# --------------------------- función genérica de VP
def vp(cf, tasas_m):
    """Valor presente descontando con las tasas_m mes a mes."""
    # factor descuento acumulado: 1/∏(1+r_m)
    df = np.cumprod(1 / (1 + tasas_m))
    return np.sum(cf * df)

# ====================== BLOQUE A  :  ESCENARIOS BASE / OPT / PES ======================
result = {}
for esc in ESC:
    # ------------- tasas mensuales
    r_short_m = (1 + rates[f"r_{esc}"]).pow(1/12) - 1          # IBR fwd
    r_mort_m  = (1 + rates[f"hipoteca_var_{esc}"]).pow(1/12) - 1

    prima_m   = SPREAD_SWAP[esc] / 12
    cuota_fija = npf.pmt(r_fija_m + prima_m, N_MESES, -MONTO)   # flujo fijo + prima

    saldo = MONTO
    cf_var, cf_fix = [], []
    for r in r_mort_m.iloc[:N_MESES]:
        interes = saldo * r
        saldo  -= MONTO / N_MESES
        cf_var.append(interes + MONTO / N_MESES)
        cf_fix.append(cuota_fija)

    # --------  Descuento **solamente con la curva IBR fwd** --------------
    vp_var = vp(np.array(cf_var), r_short_m.iloc[:N_MESES].values)
    vp_fix = vp(np.array(cf_fix), r_short_m.iloc[:N_MESES].values)

    result[esc] = dict(VPN_variable=vp_var,
                       VPN_fija=vp_fix,
                       Ahorro_swap=vp_fix - vp_var,
                       Ahorro_pct=(vp_fix - vp_var) / vp_var)

df_res = pd.DataFrame(result).T

# ------------------------- impresión ‘linda’ en consola ------------------------------
print("\n----- BLOQUE 2  –  RESULTADOS (COP) -----\n")
show = df_res.copy()
for col in ("VPN_variable", "VPN_fija", "Ahorro_swap"):
    show[col] = show[col].map(lambda x: f"{x:,.0f}")
show["Ahorro_pct"] = show["Ahorro_pct"].map(lambda x: f"{x:.2%}")
print(show[["VPN_variable", "VPN_fija", "Ahorro_swap", "Ahorro_pct"]])

df_res.to_csv("bloque2_resultados.csv", index=True)

# --------------------------- gráfico principal ---------------------------------------
plt.figure(figsize=(6,4))
bars = plt.bar(df_res.index, df_res["Ahorro_swap"]/1e6,
               color=plt.cm.Set3.colors[:3])
plt.ylabel("Ahorro vía swap (millones COP)")
plt.title("Valor presente del ahorro con swap (180 m)")
plt.axhline(0, color="k", lw=.8)

for bar in bars:
    y = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2,
             y + 0.5,
             f"{y:,.1f}",
             ha="center", va="bottom")

plt.tight_layout()
fig_path = FIG_DIR / "ahorro_bar_bloque2.png"
plt.savefig(fig_path, dpi=150)
print(f"🖼️  Figura guardada en {fig_path.relative_to(Path.cwd())}")
plt.show()

# =====================================================================================
#                     BLOQUE B :  TORNADO PLOT (sensibilidad al spread)
# =====================================================================================
spreads_pb = np.arange(150, 351, 50)   # 150–350 pb
tornado = {}                           # dict escenario → ahorro (array len=5)

for esc in ESC:
    r_short_m = (1 + rates[f"r_{esc}"]).pow(1/12) - 1
    r_mort_m  = (1 + rates[f"hipoteca_var_{esc}"]).pow(1/12) - 1

    saldo = MONTO
    cf_var = []
    for r in r_mort_m.iloc[:N_MESES]:
        interes = saldo * r
        saldo  -= MONTO / N_MESES
        cf_var.append(interes + MONTO / N_MESES)
    cf_var = np.array(cf_var)

    ahorro = []
    for sp in spreads_pb:
        prima_m = (sp/1e4) / 12          # de pb a fracción
        cuota_fija = npf.pmt(r_fija_m + prima_m, N_MESES, -MONTO)

        cf_fix = np.full(N_MESES, cuota_fija)
        vp_var = vp(cf_var, r_short_m.iloc[:N_MESES].values)
        vp_fix = vp(cf_fix, r_short_m.iloc[:N_MESES].values)
        ahorro.append((vp_fix - vp_var)/1e6)   # millones

    tornado[esc] = ahorro

# --------------------------- tornado plot horizontal ---------------------------------
fig, ax = plt.subplots(figsize=(7,4))
width = 0.25
for i, esc in enumerate(ESC):
    ax.barh([s + i*width for s in range(len(spreads_pb))],
            tornado[esc],
            height=width,
            label=esc,
            color=plt.cm.tab10.colors[i])

ax.set_yticks([s + width for s in range(len(spreads_pb))],
              [f"{pb} pb" for pb in spreads_pb])
ax.set_xlabel("Ahorro vía swap (millones COP)")
ax.set_title("Tornado: sensibilidad del ahorro al spread del swap")
ax.legend()
plt.tight_layout()
fig_path = FIG_DIR / "tornado_bloque2.png"
plt.savefig(fig_path, dpi=150)
print(f"🖼️  Figura guardada en {fig_path.relative_to(Path.cwd())}")
plt.show()