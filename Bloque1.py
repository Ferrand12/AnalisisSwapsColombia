# Bloque1.py  ── Simulación de tasa corta y cuota variable (Colombia)
# ------------------------------------------------------------------
# • Lee latam_swaps_params.xlsx
# • Escenarios: optimista, base, pesimista
# • Modelo Vasicek: dr = α(μ – r)dt + σ dW
# • Salida: gráfico + CSV con trayectorias

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ----------- Carpeta de figuras -----------
FIGS_DIR = Path(__file__).with_name("figs_bloque1")
FIGS_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# 1. Carga de parámetros DESDE el Excel maestro
# ------------------------------------------------------------------
XL = Path(__file__).with_name("latam_swaps_params.xlsx")
if not XL.exists():
    raise FileNotFoundError(f"Excel maestro no encontrado: {XL}")

row = (
    pd.read_excel(XL)
    .set_index("Country")
    .loc["Colombia"]              # ⬅︎ siempre Colombia
)

alpha = row["alpha"]              # velocidad reversión
sigma_a = row["sigma"]            # volatilidad base    (ya en fracción)
sigma_m = sigma_a / np.sqrt(12)
mu    = row["mu_long_term_%"] / 100
r0    = row["ref_rate_2024_%"] / 100
spread_mortgage = row["mortgage_variable_%"] / 100 - r0   # diferencia corta-hipoteca

plazo_meses = 180
dt          = 1/12               # paso mensual
FLOOR_SPREAD = 0.05              # 5 pp sobre la tasa simulada

# ------------------------------------------------------------------
# 2. Define escenarios
# ------------------------------------------------------------------
ESC = {
    "Optimista": {"sigma": sigma_a * 0.8, "mu": mu - 0.01},
    "Base"     : {"sigma": sigma_a,       "mu": mu},
    "Pesimista": {"sigma": sigma_a * 1.2, "mu": mu + 0.01},
}

def sim_vasicek(alpha_a, mu_a, sigma_m, r0, n_steps, cap=0.015):
    """Mensual Vasicek with vol scaling and capped moves."""
    rates = np.empty(n_steps)
    r = r0
    for t in range(n_steps):
        dr_raw = alpha_a * (mu_a - r) * dt + sigma_m * np.random.normal()
        dr = np.clip(dr_raw, -cap, cap)   # ±150 pb máx por mes
        r = max(r + dr, 0.01)              # no baja de 1 %
        rates[t] = r
    return rates

# ------------------------------------------------------------------
# 3. Simula y guarda resultados
# ------------------------------------------------------------------
np.random.seed(42)  # reproducible

all_paths = []

for escenario, pars in ESC.items():
    path = sim_vasicek(alpha, pars["mu"], sigma_m, r0, plazo_meses)
    hipoteca_var = np.maximum(path + spread_mortgage, path + FLOOR_SPREAD)

    all_paths.append(
        pd.DataFrame(
            {
                "Mes": np.arange(1, plazo_meses + 1),
                f"r_{escenario}": path,
                f"hipoteca_var_{escenario}": hipoteca_var,
            }
        )
    )

df_out = all_paths[0]
for extra in all_paths[1:]:
    df_out = df_out.merge(extra, on="Mes")

csv_out = Path(__file__).with_name("sim_rates_bloque1.csv")
df_out.to_csv(csv_out, index=False)
print(f"✅ Trayectorias guardadas en {csv_out.name}")

# ------------------------------------------------------------------
# 4‑bis. Estadísticas rápidas para validar cada escenario
# ------------------------------------------------------------------
for escenario in ESC:
    serie = df_out[f"hipoteca_var_{escenario}"]
    print(
        f"{escenario:10s} | media: {serie.mean()*100:6.2f} %  "
        f"p5: {np.percentile(serie,5)*100:6.2f} %  "
        f"p95: {np.percentile(serie,95)*100:6.2f} %"
    )

# ------------------------------------------------------------------
# 5. Gráfico de las trayectorias  +  guardado PNG
# ------------------------------------------------------------------
plt.figure(figsize=(10, 5))
for escenario in ESC:
    plt.plot(
        df_out["Mes"],
        df_out[f"hipoteca_var_{escenario}"] * 100,   # a %
        label=f"Hipoteca variable {escenario}"
    )

plt.title("Tasa hipotecaria variable simulada (Colombia)")
plt.xlabel("Mes")
plt.ylabel("Tasa anual efectiva (%)")
plt.legend()
plt.tight_layout()

# --- guardar y mostrar ---
png_path = FIGS_DIR / "trayectorias_bloque1.png"
plt.savefig(png_path, dpi=150)
print(f"🖼️  Figura guardada en {png_path.relative_to(Path.cwd())}")

plt.show()