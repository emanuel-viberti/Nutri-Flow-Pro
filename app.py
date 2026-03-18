import streamlit as st
import json
import random

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Nutri-Flow Pro v3", layout="wide")

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
    "Logística": {
        "Almuerzo en Trabajo": "at"
    }
}

# --- 2. FUNCIONES ---
def filtrar_platos(lista, tags_requeridos):
    if not lista: return []
    if not tags_requeridos: return lista
    # Normalizamos tags para que 'db' funcione como 'db2' y 'ls' como 'lf'
    def normalizar(ts):
        res = []
        for t in ts:
            if t == 'db': res.append('db2')
            elif t == 'ls': res.append('lf')
            else: res.append(t)
        return res

    filtrados = []
    for p in lista:
        p_tags = normalizar(p.get('tags', []))
        if all(t in p_tags for t in tags_requeridos):
            filtrados.append(p)
    return filtrados

def obtener_diagnostico_imc(imc):
    if imc < 18.5: return "Bajo Peso", "normal"
    if imc < 25: return "Normopeso", "normal"
    if imc < 30: return "Sobrepeso", "inverse"
    return "Obesidad", "inverse"

# --- 3. SIDEBAR ---
st.sidebar.header("👤 Perfil del Paciente")
nombre = st.sidebar.text_input("Nombre", "Paciente")
sexo = st.sidebar.selectbox("Sexo", ["Femenino", "Masculino"])
edad = st.sidebar.number_input("Edad", 18, 100, 30)
peso_actual = st.sidebar.number_input("Peso Actual (kg)", 30.0, 250.0, 75.0)
talla = st.sidebar.number_input("Talla (cm)", 100, 250, 170)

imc = peso_actual / ((talla/100)**2)
diag, color_delta = obtener_diagnostico_imc(imc)
st.sidebar.metric("IMC Actual", f"{imc:.1f}", diag, delta_color=color_delta)

st.sidebar.markdown("---")
pi_base = talla - (105 if sexo == "Femenino" else 100)
peso_ideal = st.sidebar.number_input("Peso Objetivo (Broca)", value=float(pi_base))

act_mult = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
actividad = st.sidebar.selectbox("Actividad", list(act_mult.keys()))
tmb = (10 * peso_ideal) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_sugeridas = int(tmb * act_mult[actividad])

st.sidebar.header("🧪 Macros")
p_prot = st.sidebar.slider("% Prot", 10, 40, 25)
p_gras = st.sidebar.slider("% Gras", 10, 40, 25)
p_carb = 100 - p_prot - p_gras
st.sidebar.info(f"Carbohidratos: {p_carb}%")
usar_colaciones = st.sidebar.checkbox("Incluir 2 Colaciones", True)

# --- 4. FILTROS ---
st.header("📋 Parámetros del Plan")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    f_med = st.multiselect("Restricciones Médicas", list(MAPEO_FILTROS["Médicos (Excluyentes)"].keys()))
with col_f2:
    f_pre = st.multiselect("Preferencias", list(MAPEO_FILTROS["Preferencias"].keys()))
with col_f3:
    f_log = st.multiselect("Logística", list(MAPEO_FILTROS["Logística"].keys()))

kcal_obj = st.number_input("Calorías Objetivo Diarias", value=kcal_sugeridas)

# --- 5. CARGA Y GENERACIÓN ---
try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    # Buscamos las claves sin importar mayúsculas
    listado_des = db.get('desayunos', db.get('Desayunos', []))
    listado_com = db.get('comidas', db.get('Comidas', []))
    listado_col = db.get('colaciones', db.get('Colaciones', []))

    tags_base = [MAPEO_FILTROS["Médicos (Excluyentes)"][f] for f in f_med] + \
                 [MAPEO_FILTROS["Preferencias"][f] for f in f_pre]
    
    p_des = filtrar_platos(listado_des, tags_base)
    p_com_full = filtrar_platos(listado_com, tags_base)
    p_col = filtrar_platos(listado_col, tags_base)

    # Si por los filtros no hay colaciones, agregamos genéricas seguras
    if not p_col and usar_colaciones:
        p_col = [{"nombre": "Fruta de estación", "kcal": 80, "tags": ["gf", "db2", "lf", "hta", "at"]}]

    tag_at = [MAPEO_FILTROS["Logística"]["Almuerzo en Trabajo"]]
    almuerzo_trabajo = "Almuerzo en Trabajo" in f_log

    if st.button("🚀 Generar Plan Semanal"):
        if not p_des or not p_com_full:
            st.error("No hay platos suficientes con estos filtros.")
        else:
            plan = {}
            for dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]:
                mejor = None
                min_err = 9999
                ops_alm = filtrar_platos(p_com_full, tag_at) if almuerzo_trabajo else p_com_full
                if not ops_alm: ops_alm = p_com_full

                for _ in range(500):
                    d, a, m, c = random.choice(p_des), random.choice(ops_alm), random.choice(p_des), random.choice(p_com_full)
                    c1 = random.choice(p_col) if usar_colaciones else {"nombre": "-", "kcal": 0}
                    c2 = random.choice(p_col) if usar_colaciones else {"nombre": "-", "kcal": 0}
                    
                    total = d['kcal'] + a['kcal'] + m['kcal'] + c['kcal'] + c1['kcal'] + c2['kcal']
                    if abs(total - kcal_obj) < min_err:
                        min_err = abs(total - kcal_obj)
                        mejor = {"D": d, "C1": c1, "A": a, "M": m, "C2": c2, "C": c, "Total": total}
                plan[dia] = mejor
            st.session_state['plan'] = plan

    if 'plan' in st.session_state:
        plan = st.session_state['plan']
        cols = st.columns(7)
        for i, (dia, p) in enumerate(plan.items()):
            with cols[i]:
                st.subheader(dia)
                st.metric("Total", f"{p['Total']} kcal")
                st.write(f"**D:** {p['D']['nombre']}")
                if usar_colaciones: st.caption(f"C1: {p['C1']['nombre']}")
                st.success(f"**A:** {p['A']['nombre']}")
                st.write(f"**M:** {p['M']['nombre']}")
                if usar_colaciones: st.caption(f"C2: {p['C2']['nombre']}")
                st.success(f"**C:** {p['C']['nombre']}")

except Exception as e:
    st.error(f"Error crítico: {e}")
