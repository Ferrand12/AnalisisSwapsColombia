README ‧ AnalisisSwapsColombia

Simulaciones Vasicek, valoración de swaps hipotecarios y análisis de riesgo para el mercado colombiano (2015-2024).

⸻

0. Motivación

Los créditos hipotecarios en Colombia suelen indexarse a tasas variables (IBR 3 M, DTF o UVR).
Para protegerse contra la volatilidad de las tasas, un banco o un originador puede cubrirse pagando una tasa fija y recibiendo la tasa variable – es decir, usando un swap de tasas de interés.
El objetivo del proyecto es cuantificar:
	1.	Ahorro (valor presente) al adoptar un swap (pagar fijo ↔ recibir variable).
	2.	Sensibilidad de dicho ahorro al spread del swap.
	3.	Riesgo de mercado → VaR del ahorro a 12 meses.

Todo se replica para tres escenarios macro: Optimista, Base y Pesimista.

⸻

1. Datos de entrada

Fuente	Archivo	Variable clave	Descripción
latam_swaps_params.xlsx	latam_swaps_params.xlsx	α, σ, μ, r0	Parámetros Vasicek y spreads mensuales derivados de reportes Banrep & SuperFinanciera
Spread maestro	spread_maestro.xlsx (hoja Spreads)	spread_Optimista, spread_Base, spread_Pesimista	Se construye a partir de IBR 3M (dic-2024) y tasas hipotecarias promedio (may-2024).
Trayectorias simuladas	sim_rates_bloque1.csv	r_* y hipoteca_var_*	Guardado por el Bloque 1.
Resultados intermedios	bloque2_resultados.csv	Ahorro swap 180 m + sensibilidad	Salida del Bloque 2.

Reproducibilidad
Todos los datos crudos (series Banrep, SuperFinanciera) se levantaron con pandas-datareader y se fijan al 31-dic-2024.
Las hojas de Excel solo almacenan el snapshot para no depender de APIs externas en cada corrida.

⸻

2. Metodología paso a paso

Bloque 1 – Simulación de la tasa corta + hipoteca variable
	1.	Modelo Vasicek mensual

dr_t = α(μ − r_t)Δt + σ√Δt ϵ_t

Cap mensual: ±150 pb para reflejar shocks realistas.

	2.	Tres escenarios cambiando μ (±100 pb) y σ (±20 %).
	3.	Se suma el spread hipotecario histórico → hipoteca_var_*.
	4.	Salida:
	•	sim_rates_bloque1.csv
	•	figs_bloque1/trayectorias_bloque1.png

Bloque 2 – Ahorro PV vs swap (180 meses) + tornado
	1.	Se calcula la cuota nivelada (función pmt) de dos flujos:
	•	Variable: hipoteca_var_*
	•	Fija    : hipoteca_var_* + spread swap
	2.	Se descuentan flujos a 10 % EA para obtener el VPN de cada deuda.
	3.	Ahorro = PV(variable) – PV(fija).
	4.	Se hace sensibilidad 150–350 pb y tornado plot.
	5.	Salida:
	•	bloque2_resultados.csv
	•	figs_bloque2/ahorro_bar_bloque2.png
	•	figs_bloque2/tornado_bloque2.png

Bloque 3 – Ahorro % y comparativo
	1.	Convierte ahorro absoluto a % del saldo vivo.
	2.	Genera gráfico combinado de columnas (ahorro MM) y línea (ahorro %).
	3.	Salida: figs_bloque3/ahorro_swap_bloque3.png

Bloque 4 – VaR 95 % del ahorro (12 meses)
	1.	Re-calibración Vasicek a los últimos 12 m (estimación kappa, μ, σ).
	2.	Monte Carlo 10 000 trayectorias sobre 12 m.
	3.	Para cada path:
	•	Calcula cuota variable y cuota fija ⇢ ahorro path.
	•	Obtiene distribución de ahorros.
	4.	VaR 95 % = percentil 5 %.
	5.	Salida:
	•	Histograma por escenario (figs_bloque4/hist_*.png)
	•	Barras comparativas (figs_bloque4/VaR_comparativo.png)
	•	Tabla resumen → bloque4_VaR.csv

⸻

3. Estructura de carpetas

AnalisisSwapsColombia/
├── ManuelaSanchez_codigo_swaps/   # código
│   ├── Bloque1.py
│   ├── Bloque2.py
│   ├── Bloque3.py
│   ├── Bloque4.py
│   ├── config_swaps.py
│   └── datos.py
├── data/                          # insumos y outputs tabulares
│   ├── latam_swaps_params.xlsx
│   ├── spread_maestro.xlsx
│   ├── sim_rates_bloque1.csv
│   ├── bloque2_resultados.csv
│   └── bloque4_VaR.csv
├── figs_bloque1/
├── figs_bloque2/
├── figs_bloque3/
├── figs_bloque4/
└── docs/
    └── Explicacion_graficas_swaps.docx


⸻

4. Dependencias

numpy>=1.26
pandas>=2.1
matplotlib>=3.8
openpyxl         # leer/escribir .xlsx

Instalación:

pip install -r requirements.txt

Para reproducir exactamente los gráficos, utiliza Python 3.10+ (probado en 3.10, 3.11).

⸻

5. Cómo ejecutar todo el pipeline

python codigo_swaps/Bloque1.py
python codigo_swaps/Bloque2.py
python codigo_swaps/Bloque3.py
python codigo_swaps/Bloque4.py

Después de cada bloque encontrarás los PNG en la carpeta correspondiente y los CSV en data/.

⸻

6. Interpretación de las figuras clave

Figura	Insight principal
trayectorias_bloque1.png	Evolución simulada de la tasa hipotecaria variable. Permite visualizar volatilidad y diferencias por escenario.
ahorro_bar_bloque2.png	Ahorro (PV) en todo el plazo. Muestra que, en promedio, el escenario Optimista otorga el mayor beneficio absoluto.
tornado_bloque2.png	Mide sensibilidad del ahorro al spread del swap; identifica el rango donde la cobertura deja de ser atractiva.
ahorro_swap_bloque3.png	Combina ahorro MM y % respecto al saldo; facilita comunicar eficiencia relativa de la cobertura.
Hist_ (bloque 4)*	Distribución Monte Carlo del ahorro a 12 m; la línea roja = VaR 95 %. Sirve para cuantificar riesgo de “ahorro menor al esperado”.
VaR_comparativo.png	Resume VaR absoluto entre escenarios → mayor riesgo en Pesimista.


⸻

7. Limitaciones y próximos pasos
	•	Modelo de tasas: se usa Vasicek simple; podría migrarse a CIR o HW1F calibrado a la curva TES.
	•	Correlaciones: actualmente los escenarios son independientes; se puede enlazar con inflación y spread soberano.
	•	Liquidez del swap: no incorpora CVA/DVA ni ajustes de funding.
	•	Back-testing: integrar datos históricos de swaps ON-OIS vs IBR para validar spread estructural.

⸻

8. Contribuciones
	1.	Fork & Pull Request: Describe la mejora (código limpio, nuevo bloque, actualización de datos).
	2.	Issues: Etiqueta como bug, enhancement o question.
	3.	Licencia: MIT — usa y adapta, dando crédito.

⸻

9. Referencias
	•	Banco de la República (2024). Serie IBR 3 M.
	•	Superintendencia Financiera de Colombia (2024). Reporte Tasas Hipotecarias.
	•	Hull, J. (2022). Options, Futures and Other Derivatives.
	•	Hannan, A. (2023). “Swap spreads in EM mortgage markets”, Journal of Fixed Income.

⸻


<p align="center"><b>Listo para clonar, correr y analizar.</b></p>
