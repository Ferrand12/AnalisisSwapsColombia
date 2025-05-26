"""
datos_colombia.py
=================
Centraliza **solo** los parámetros de *Colombia* que alimentan todos los
bloques del proyecto de swaps hipotecarios.  Su misión es tomar la tabla
maestra `latam_swaps_params.xlsx`, extraer la fila de Colombia, normalizar
las unidades y dejar todo listo para que los demás scripts no tengan que
volver a leer el Excel.

Salida del script
-----------------
Al ejecutarlo crea dos artefactos en la misma carpeta:

1. **`params_colombia.json`**  – Diccionario con todos los parámetros que
   usa el resto del código (tasas, volatildad, spreads, supuestos de cartera).
2. **`vasicek_inputs.csv`**     – Tabla 1×4 con `alpha, sigma, mu, r0`.
   Es el insumo directo para la simulación de trayectorias (Bloque 1‑2).


Uso rápido
~~~~~~~~~~
```bash
python datos_colombia.py      # genera los archivos y muestra ✅
```
Los demás bloques pueden importar la función `build_params()` o leer los
archivos JSON / CSV según convenga.
"""

from pathlib import Path
import json
import pandas as pd

# ----------------------------------------------------------------------
#  Ubicaciones de entrada y salida
# ----------------------------------------------------------------------
_EXCEL = Path(__file__).with_name("latam_swaps_params.xlsx")
_OUT_JSON = Path(__file__).with_name("params_colombia.json")
_OUT_CSV = Path(__file__).with_name("vasicek_inputs.csv")


def build_params(
    monto: float = 500_000_000,
    plazo_meses: int = 180,
    floor: float = 0.06,
) -> dict:
    """Extrae la fila *Colombia* y genera los archivos de parámetros.

    Parameters
    ----------
    monto : float
        Monto nominal de la cartera hipotecaria (COP).
    plazo_meses : int
        Plazo remanente (meses) – se usa en todos los bloques.
    floor : float
        Piso (floor) de la tasa variable expresado en proporción (0.06 = 6 %).

    Returns
    -------
    dict
        Diccionario con todos los parámetros – idéntico al JSON guardado.
    """

    # ----------------- lee Excel maestro -----------------
    if not _EXCEL.exists():
        raise FileNotFoundError(f"No se encontró el Excel maestro: {_EXCEL}")

    df = pd.read_excel(_EXCEL).set_index("Country")
    if "Colombia" not in df.index:
        raise ValueError("La hoja no contiene una fila 'Colombia'.")

    row = df.loc["Colombia"]

    # ----------------- arma el diccionario ---------------
    params = {
        "country": "Colombia",
        # cartera base
        "monto": monto,
        "plazo_meses": plazo_meses,
        "floor": floor,
        # niveles de tasas (proporción, no %)
        "r0": row["ref_rate_2024_%"] / 100,
        "swap_5y": row["swap_5y_%"] / 100,
        "swap_10y": row["swap_10y_%"] / 100,
        "mortgage_fixed": row["mortgage_fixed_%"] / 100,
        "mortgage_variable": row["mortgage_variable_%"] / 100,
        # parámetros estocásticos (Vasicek/HW)
        "alpha": row["alpha"],
        "sigma": row["sigma"],
        "mu": row["mu_long_term_%"] / 100,
        # volatilidad histórica para VaR
        "vol_annual": row["vol_annual_%"] / 100,
        # tasa de descuento ≈ media 10a de la ref.
        "discount_rate": row["ref_rate_mean10_%"] / 100,
        # spreads para Bloque 5 (costeo swap)
        "spread_swap_ref_5_pb": row["spread_swap_ref_5_pb"],
        "spread_swap_mortgage_pb": row["spread_swap_mortgage_pb"],
    }

    # ----------------- guarda artefactos -----------------
    _OUT_JSON.write_text(json.dumps(params, indent=4))

    vasicek_df = pd.DataFrame({
        "alpha": [params["alpha"    ]],
        "sigma": [params["sigma"    ]],
        "mu"   : [params["mu"       ]],
        "r0"   : [params["r0"       ]],
    })
    vasicek_df.to_csv(_OUT_CSV, index=False)

    print(f"✅ Parámetros guardados en {_OUT_JSON.name} y {_OUT_CSV.name}")
    return params


# Ejecuta si se llama como script -------------------------
if __name__ == "__main__":
    build_params()
