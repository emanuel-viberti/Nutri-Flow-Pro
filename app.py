import streamlit as st
import pandas as pd
import json
import random
from fpdf import FPDF
import io

# --- 1. CONFIGURACIÓN Y MAPPING DE FILTROS ---
st.set_page_config(page_title="Nutri-Flow Pro v2", layout="wide")

# Diccionario Maestro de Filtros (Tags que deben estar en el JSON)
MAPEO_FILTROS = {
    "Médicos (Excluyentes)": {
        "Diabetes tipo 2": "db2",
        "Dislipidemia": "dlp",
        "Hipertensión": "hta",
        "Celiaquía (Sin TACC)": "gf",
        "Intolerancia a la Lactosa": "lf",
        "Intestino Irritable (SII)": "sii",
        "Enfermedad Renal Crónica": "erc",
        "Alergia Frutos Secos": "afn",
        "Alergia al Huevo": "ahv",
        "Alergia a Mariscos": "amr",
        "Alergia a Soja": "asj"
    },
    "Preferencias": {
        "Vegetariano": "veg",
        "Vegano": "vgn",
        "Keto": "keto",
        "Paleo": "paleo"
    },
   # En el diccionario MAPEO_FILTROS
"Logística": {
    "Almuerzo en Trabajo": "at"
}

# En la lógica de generación del plan (dentro del bucle de los 1000 intentos):
# Solo filtramos por 'at' si es el Almuerzo
p_alm_filtrados = filtrar_platos(p_alm, [MAPEO_FILTROS["Logística"]["Almuerzo en Trabajo"]]) if "Almuerzo en Trabajo" in f_log else p_alm
# La cena (c) seguirá usando la lista p_alm normal sin el filtro 'at'
}

# --- 2. FUNCIONES LÓGICAS ---
def filtrar_platos(lista, tags_requeridos):
    if not tags_requeridos:
        return lista
    # Solo incluye el plato si tiene TODOS los tags seleccionados por el nutri
    return [p for p in lista if all(t in p.get('tags', []) for t in tags_requeridos)]

def calcular_macros(kcal, p_p, p_g, p_c):
    return {
        "p": round((kcal * (p_p / 100)) / 4, 1),
        "g": round((kcal * (p_g / 100)) / 9, 1),
        "c": round((kcal * (p_c / 100)) / 4, 1)
    }

def obtener_diagnostico_imc(imc):
    if imc < 18.5: return "Bajo Peso", "normal"
    if imc < 25: return "Normopeso", "normal"
    if imc < 30: return "Sobrepeso", "inverse"
    return "Obesidad", "inverse"

# --- 3. SIDEBAR: PERFIL Y CÁLCULOS ---
st.sidebar.header("👤 Perfil del Paciente")
nombre = st.sidebar.text_input("Nombre Completo", "Paciente")
sexo = st.sidebar.selectbox("Sexo", ["Femenino", "Masculino"])
edad = st.sidebar.number_input("Edad", 18, 100, 30)
peso_actual = st.sidebar.number_input("Peso Actual (kg)", 30.0, 250.0, 75.0)
talla = st.sidebar.number_input("Talla (cm)", 100, 250, 170)

# IMC con Diagnóstico
imc = peso_actual / ((talla/100)**2)
diag, color = obtener_diagnostico_imc(imc)
st.sidebar.metric("IMC Actual", f"{imc:.1f}", diag, delta_color=color)

# Peso Ideal (Broca) Editable
pi_base = talla - (105 if sexo == "Femenino" else 100)
peso_ideal = st.sidebar.number_input("Peso Ideal Objetivo (Broca)", value=float(pi_base))

# Gasto Calórico (Mifflin-St Jeor) sobre Peso Ideal
actividad = st.sidebar.selectbox("Actividad Física", ["Sedentario", "Ligero", "Moderado", "Intenso"])
mults = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
tmb = (10 * peso_ideal) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_sugeridas = int(tmb * mults[actividad])

st.sidebar.markdown("---")
st.sidebar.header("🧪 Configuración Dietaria")
p_prot = st.sidebar.slider("% Proteína", 10, 40, 20)
p_gras = st.sidebar.slider("% Grasas", 10, 40, 30)
p_carb = 100 - p_prot - p_gras
st.sidebar.info(f"Carbohidratos: {p_carb}%")

usar_colaciones = st.sidebar.checkbox("Incluir 2 Colaciones", True)

# --- 4. SELECCIÓN DE FILTROS ---
st.header("📋 Selección de Filtros")
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    f_med = st.multiselect("Restricciones Médicas (Duras)", list(MAPEO_FILTROS["Médicos (Excluyentes)"].keys()))
with col_f2:
    f_pre = st.multiselect("Preferencias", list(MAPEO_FILTROS["Preferencias"].keys()))
with col_f3:
    f_log = st.multiselect("Logística", list(MAPEO_FILTROS["Logística"].keys()))

# Consolidar todos los tags seleccionados
tags_finales = [MAPEO_FILTROS["Médicos (Excluyentes)"][f] for f in f_med] + \
               [MAPEO_FILTROS["Preferencias"][f] for f in f_pre] + \
               [MAPEO_FILTROS["Logística"][f] for f in f_log]

# --- 5. CARGA Y GENERACIÓN ---
try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    # Filtrado dinámico
    p_des = filtrar_platos(db['desayunos'], tags_finales)
    p_alm = filtrar_platos(db['comidas'], tags_finales)
    p_cen = filtrar_platos(db['comidas'], tags_finales)
    p_col = filtrar_platos(db.get('colaciones', []), tags_finales)

    st.write(f"📊 **Disponibilidad:** Desayunos ({len(p_des)}) | Almuerzos/Cenas ({len(p_alm)}) | Colaciones ({len(p_col)})")
    
    kcal_obj = st.number_input("Calorías Objetivo Diarias", value=kcal_sugeridas)

    if st.button("🚀 Generar Plan Semanal"):
        if not p_des or not p_alm:
            st.error("No hay platos que cumplan con TODOS los filtros seleccionados.")
        else:
            plan = {}
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            for dia in dias:
                # Lógica de selección aleatoria con ajuste calórico
                res = None
                min_err = 9999
                for _ in range(500):
                    d = random.choice(p_des)
                    a = random.choice(p_alm)
                    m = random.choice(p_des)
                    c = random.choice(p_cen)
                    c1 = random.choice(p_col) if (usar_colaciones and p_col) else {"nombre": "-", "kcal": 0}
                    c2 = random.choice(p_col) if (usar_colaciones and p_col) else {"nombre": "-", "kcal": 0}
                    
                    actual = d['kcal'] + a['kcal'] + m['kcal'] + c['kcal'] + c1['kcal'] + c2['kcal']
                    if abs(actual - kcal_obj) < min_err:
                        min_err = abs(actual - kcal_obj)
                        res = {"D": d, "C1": c1, "A": a, "M": m, "C2": c2, "C": c, "Total": actual}
                plan[dia] = res
            st.session_state['plan'] = plan

    # --- 6. MOSTRAR RESULTADOS ---
    if 'plan' in st.session_state:
        plan = st.session_state['plan']
        cols = st.columns(7)
        for i, (dia, platos) in enumerate(plan.items()):
            with cols[i]:
                st.subheader(dia)
                st.metric("Total", f"{platos['Total']} kcal")
                st.write(f"**D:** {platos['D']['nombre']}")
                if usar_colaciones: st.caption(f"C1: {platos['C1']['nombre']}")
                st.success(f"**A:** {platos['A']['nombre']}")
                st.write(f"**M:** {platos['M']['nombre']}")
                if usar_colaciones: st.caption(f"C2: {platos['C2']['nombre']}")
                st.success(f"**C:** {platos['C']['nombre']}")

except Exception as e:
    st.warning(f"Esperando carga de datos o error en JSON: {e}")
