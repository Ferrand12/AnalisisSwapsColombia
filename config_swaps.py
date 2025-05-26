

"""
config_swaps.py

Lectura centralizada de los parámetros que alimentan todas las
simulaciones del proyecto de swaps hipotecarios.

* Usa el Excel `latam_swaps_params.xlsx` (una sola hoja) generado
  durante la fase de recolección de datos.
* Devuelve un diccionario con las variables clave ya normalizadas.
"""

import os
from pathlib import Path
import pandas as pd

# ----------------------------------------------------------------------
# RUTA POR DEFECTO: el Excel con la tabla maestra (mismo directorio)
# ----------------------------------------------------------------------
_EXCEL_DEFAULT = "latam_swaps_params.xlsx"


def get_params(
    country: str = "Colombia",
    excel_path: str | os.PathLike | None = None,
    monto: float = 500_000_000,
    plazo_meses: int = 180,
    floor: float = 0.06,
) -> dict:
    """
    Devuelve un diccionario con los parámetros de simulación
    para el *country* solicitado.

    Parameters
    ----------
    country : str
        Nombre del país tal cual aparece en la columna 'Country'
        del Excel (no sensible a mayúsculas/minúsculas).
    excel_path : str | Path | None
        Ruta al archivo de parámetros.  Si es None se usa _EXCEL_DEFAULT
        ubicado en el mismo directorio que este módulo.
    monto : float
        Monto nominal del portafolio hipotecario (COP).
    plazo_meses : int
        Plazo remanente de la cartera (meses).
    floor : float
        Piso de la tasa variable (como proporción, e.g. 0.06 = 6 %).

    Returns
    -------
    dict
        Con llaves:
        'monto', 'plazo_meses', 'floor',
        'tasa_inicial', 'tasa_swap',
        'vol_annual', 'alpha', 'sigma', 'mu',
        'mortgage_fixed', 'mortgage_variable',
        'country'
    """
    country = country.capitalize()

    # ------------- localiza el Excel -----------------
    if excel_path is None:
        excel_path = Path(__file__).with_name(_EXCEL_DEFAULT)
    else:
        excel_path = Path(excel_path)

    if not excel_path.exists():
        raise FileNotFoundError(f"No se encontró el Excel: {excel_path}")

    # ------------- lee la hoja -----------------------
    df = pd.read_excel(excel_path)
    df = df.set_index("Country")

    if country not in df.index:
        raise ValueError(f"País '{country}' no encontrado en {excel_path}")

    row = df.loc[country]

    # ------------- construye el dict -----------------
    return {
        # parámetros de cartera
        "monto": monto,
        "plazo_meses": plazo_meses,
        "floor": floor,
        "country": country,
        # niveles de tasas (en proporción, no %)
        "tasa_inicial": row["ref_rate_2024_%"] / 100,
        "tasa_swap": row["swap_10y_%"] / 100,
        "mortgage_fixed": row["mortgage_fixed_%"] / 100,
        "mortgage_variable": row["mortgage_variable_%"] / 100,
        # parámetros estocásticos
        "alpha": row["alpha"],
        "sigma": row["sigma"],               # ya es porcentual (0.035 == 3.5 %)
        "mu": row["mu_long_term_%"] / 100,
        "vol_annual": row["vol_annual_%"] / 100,
    }