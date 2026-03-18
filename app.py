import streamlit as st
import json
import random
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Nutri-Flow Pro", layout="wide")

# REEMPLAZA ESTA URL con el botón "Raw" de tu GitHub
URL_JSON = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/platos.json"

MAPEO_FILTROS = {
    "Médicos": {
        "Diabetes tipo 2": "db2", "Dislipidemia": "dlp", "Hipertensión": "hta",
        "Celiaquía": "gf", "Lactosa": "lf", "Frutos Secos": "afn"
    },
    "Logística": {"Almuerzo en Trabajo": "at"}
}

# --- 2. FUNCIONES DE CARGA Y FILTRADO ---
@st.cache_data
def cargar_datos(url):
    try:
        # Si prefieres local, usa: with open('./data/platos.json') as f: return json.load(f)
        response = requests.get(url)
        return response.json()
    except:
        return None

def filtrar_platos(lista, tags_req):
    if not lista: return []
    def norm(ts):
        # Mapeo de compatibilidad para tags viejos (db -> db2, ls -> lf)
        m = {'db': 'db2', 'ls': 'lf', 'tp': 'at'}
        return [m.get(t, t) for t in ts]
    return [p for p in lista if all(t in norm(p.get('tags', [])) for t in tags_req)]

# --- 3. SIDEBAR (Como en tu foto) ---
st.sidebar.header("👤 Perfil Paciente")
peso = st.sidebar.number_input("Peso (kg)", 30.0, 150.0, 75.0)
talla = st.sidebar.number_input("Talla (cm)", 100, 220, 170)
sexo = st.sidebar.selectbox("Sexo", ["Femenino", "Masculino"])
edad = st.sidebar.number_input("Edad", 18, 90, 30)

imc = peso / ((talla/100)**2)
st.sidebar.metric("IMC Actual", f"{imc:.1f}")

pi = talla - (105 if sexo == "Femenino" else 100)
peso_obj = st.sidebar.number_input("Peso Objetivo", value=float(pi))

usar_col = st.sidebar.checkbox("Incluir 2 Colaciones", True)

# --- 4. CUERPO PRINCIPAL ---
st.title("🍎 Generador de Plan Nutricional")
col1, col2 = st.columns(2)
with col1:
    f_med = st.multiselect("Restricciones Médicas", list(MAPEO_FILTROS["Médicos"].keys()))
with col2:
    f_log = st.multiselect("Logística", list(MAPEO_FILTROS["Logística"].keys()))

kcal_obj = st.number_input("Kcal Objetivo", value=2000)

db = cargar_datos(URL_JSON)

if db and st.button("🚀 Generar Plan Semanal"):
    tags_base = [MAPEO_FILTROS["Médicos"][f] for f in f_med]
    es_at = "Almuerzo en Trabajo" in f_log
    
    # Preparar listas
    p_des = filtrar_platos(db.get('desayunos', []), tags_base)
    p_com = filtrar_platos(db.get('comidas', []), tags_base)
    p_col = filtrar_platos(db.get('colaciones', []), tags_base)

    if p_des and p_com:
        plan = {}
        for dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]:
            ops_alm = filtrar_platos(p_com, ["at"]) if es_at else p_com
            # Lógica de selección por cercanía a Kcal (500 intentos)
            mejor = None
            diff = 9999
            for _ in range(500):
                d, a, m, c = random.choice(p_des), random.choice(ops_alm or p_com), random.choice(p_des), random.choice(p_com)
                c1 = random.choice(p_col) if (usar_col and p_col) else {"nombre": "-", "kcal": 0}
                c2 = random.choice(p_col) if (usar_col and p_col) else {"nombre": "-", "kcal": 0}
                total = d['kcal'] + a['kcal'] + m['kcal'] + c['kcal'] + c1['kcal'] + c2['kcal']
                if abs(total - kcal_obj) < diff:
                    diff = abs(total - kcal_obj)
                    mejor = {"D": d, "A": a, "M": m, "C": c, "C1": c1, "C2": c2, "Total": total}
            plan[dia] = mejor
        st.session_state['plan'] = plan

# --- 5. RENDERIZADO DE TARJETAS (Diseño igual a tu foto) ---
if 'plan' in st.session_state:
    cols = st.columns(7)
    for i, (dia, p) in enumerate(st.session_state['plan'].items()):
        with cols[i]:
            st.markdown(f"### {dia}")
            st.info(f"**{p['Total']} kcal**")
            st.write(f"**Des:** {p['D']['nombre']}")
            if usar_col: st.caption(f"C1: {p['C1']['nombre']}")
            st.success(f"**Alm:** {p['A']['nombre']}")
            st.write(f"**Mer:** {p['M']['nombre']}")
            if usar_col: st.caption(f"C2: {p['C2']['nombre']}")
            st.success(f"**Cena:** {p['C']['nombre']}")
