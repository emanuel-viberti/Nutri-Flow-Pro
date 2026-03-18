import streamlit as st
import pandas as pd
import json
import random
import plotly.express as px
# Función de filtrado profesional
def filtrar_platos(lista, filtros):
    if not filtros:
        return lista
    return [p for p in lista if all(f in p.get('tags', []) for f in filtros)]
# Configuración
st.set_page_config(page_title="Nutri-Flow Pro", layout="wide")

# --- 1. SIDEBAR: PANEL DE CONTROL ---
st.sidebar.header("📋 Datos del Paciente")
nombre = st.sidebar.text_input("Nombre", value="Paciente")
sexo = st.sidebar.selectbox("Sexo", ["Femenino", "Masculino"])
peso_actual = st.sidebar.number_input("Peso Actual (kg)", value=77.0)
talla = st.sidebar.number_input("Talla (cm)", value=170)
edad = st.sidebar.number_input("Edad", value=30)
actividad = st.sidebar.selectbox("Actividad Física", ["Sedentario", "Ligero", "Moderado", "Intenso"])

# --- CÁLCULOS ANTROPOMÉTRICOS ---
# 1. IMC y Diagnóstico Visual
imc = peso_actual / ((talla/100) ** 2)
if imc < 18.5: 
    diag, color = "Bajo Peso", "inverse"
elif 18.5 <= imc < 25: 
    diag, color = "Normopeso", "normal"
elif 25 <= imc < 30: 
    diag, color = "Sobrepeso", "off"
else: 
    diag, color = "Obesidad", "inverse"

st.sidebar.metric("IMC Actual", f"{imc:.1f}", diag, delta_color=color)

# 2. Peso Ideal Editable (Base Broca)
pi_sugerido = talla - 100 if sexo == "Masculino" else talla - 105
peso_ideal = st.sidebar.number_input("Peso Ideal Objetivo (kg)", value=float(pi_sugerido), help="Calculado por Broca, pero puedes editarlo.")

# --- 2. CÁLCULOS DE ENERGÍA (Basados en PESO IDEAL) ---
act_mult = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
# Usamos peso_ideal aquí para las Kcal recomendadas
tmb_pi = (10 * peso_ideal) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_recomendadas = int(tmb_pi * act_mult[actividad])

# --- SECCIÓN DE MACROS EN SIDEBAR (REORGANIZADA) ---
st.sidebar.markdown("---")
st.sidebar.header("📊 Distribución de Macros")

# 1. Primero definimos los que son manuales
p_prot = st.sidebar.slider("% Proteína", 10, 50, 20, step=5)
p_gras = st.sidebar.slider("% Grasas", 10, 50, 30, step=5)

# 2. DESPUÉS definimos p_carb para que siempre exista antes de usarse
p_carb = 100 - p_prot - p_gras

# 3. Ahora sí podemos hacer validaciones con p_carb
if p_carb < 0:
    st.sidebar.error("⚠️ La suma supera el 100%. Bajá Proteína o Grasas.")
    p_carb = 0
else:
    st.sidebar.success(f"**Carbohidratos: {p_carb}%**")

# Gráfico de Torta (Pie Chart)
df_macros = pd.DataFrame({"Macro": ["P", "G", "C"], "Val": [p_prot, p_gras, p_carb]})
fig_macros = px.pie(df_macros, values='Val', names='Macro', hole=0.4, height=200)
fig_macros.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
st.sidebar.plotly_chart(fig_macros, use_container_width=True)

# --- OPCIÓN DE COLACIONES ---
st.sidebar.markdown("---")
usar_colaciones = st.sidebar.checkbox("¿Incluir Colaciones? (Plan 6 comidas)", value=True)

# --- 4. CUERPO PRINCIPAL ---
st.title(f"Plan Nutricional: {nombre}")

col1, col2 = st.columns(2)
with col1:
    # El valor por defecto ahora viene del cálculo con Peso Ideal
    kcal_final = st.number_input("Calorías Objetivo Diarias", value=kcal_recomendadas)
    st.caption(f"💡 Sugerencia basada en Peso Ideal ({peso_ideal}kg): {kcal_recomendadas} kcal")

with col2:
    st.write(f"**Distribución en Gramos:**")
    g_p = int((kcal_final*p_prot/100)/4)
    g_g = int((kcal_final*p_gras/100)/9)
    g_c = int((kcal_final*p_carb/100)/4)
    st.info(f"P: {g_p}g | G: {g_g}g | C: {g_c}g")

import streamlit as st
import pandas as pd
import json
import random
import plotly.express as px

# ... (Configuración inicial, Sidebar de Datos e IMC se mantienen igual) ...

# --- 5. FILTROS Y CARGA DE DATOS ---
st.sidebar.markdown("---")
pat_map = {
    "Diabetes (db)": "db", 
    "Sin TACC (gf)": "gf", 
    "Bajo Sodio (ls)": "ls", 
    "Vegano (vgn)": "vgn", 
    "Vegetariano (veg)": "veg", 
    "Almuerzo para Tupper (tp)": "tp"
}
seleccion = st.sidebar.multiselect("Filtros Médicos:", options=list(pat_map.keys()))

# ... (Todo el código anterior de Sidebar y cálculos se mantiene igual) ...

try:  # <--- Nivel 0
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    # ... (filtros y pools de platos) ...

    if st.button("🚀 Generar Plan Semanal"): # <--- Nivel 1 (dentro del try)
        if not p_des or not p_alm: # <--- Nivel 2
            st.error("No hay platos...")
        else: # <--- Nivel 2
            cols = st.columns(7)
            # ... resto del código ...
            for i, dia in enumerate(dias): # <--- Nivel 3
                with cols[i]: # <--- Nivel 4
                    # ... lógica de random ...
