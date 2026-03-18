import streamlit as st
import json
import random

# --- 1. CONFIGURACIÓN Y MAPEO ---
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

# --- 2. FUNCIONES AUXILIARES ---
def filtrar_platos(lista, tags_requeridos):
    if not lista: return []
    if not tags_requeridos: return lista
    return [p for p in lista if all(t in p.get('tags', []) for t in tags_requeridos)]

def obtener_diagnostico_imc(imc):
    if imc < 18.5: return "Bajo Peso", "normal"
    if imc < 25: return "Normopeso", "normal"
    if imc < 30: return "Sobrepeso", "inverse"
    return "Obesidad", "inverse"

# --- 3. SIDEBAR: PERFIL, IMC Y PESO IDEAL EDITABLE ---
st.sidebar.header("👤 Perfil del Paciente")
nombre = st.sidebar.text_input("Nombre", "Paciente")
sexo = st.sidebar.selectbox("Sexo", ["Femenino", "Masculino"])
edad = st.sidebar.number_input("Edad", 18, 100, 30)
peso_actual = st.sidebar.number_input("Peso Actual (kg)", 30.0, 250.0, 75.0)
talla = st.sidebar.number_input("Talla (cm)", 100, 250, 170)

# CÁLCULO IMC
imc = peso_actual / ((talla/100)**2)
diag, color_delta = obtener_diagnostico_imc(imc)
st.sidebar.metric("IMC Actual", f"{imc:.1f}", diag, delta_color=color_delta)

st.sidebar.markdown("---")
# PESO IDEAL BROCA (EDITABLE)
pi_base = talla - (105 if sexo == "Femenino" else 100)
peso_ideal = st.sidebar.number_input("Peso Ideal Objetivo (Broca)", value=float(pi_base))

# GASTO CALÓRICO BASADO EN PESO IDEAL
act_mult = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
actividad = st.sidebar.selectbox("Actividad", list(act_mult.keys()))
tmb = (10 * peso_ideal) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_sugeridas = int(tmb * act_mult[actividad])

st.sidebar.markdown("---")
st.sidebar.header("🧪 Configuración de Macros")
p_prot = st.sidebar.slider("% Prot", 10, 40, 25)
p_gras = st.sidebar.slider("% Gras", 10, 40, 25)
p_carb = 100 - p_prot - p_gras
st.sidebar.info(f"Carbohidratos: {p_carb}%")

usar_colaciones = st.sidebar.checkbox("Incluir 2 Colaciones", True)

# --- 4. FILTROS ---
st.header("📋 Parámetros del Plan Nutricional")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    f_med = st.multiselect("Restricciones Médicas", list(MAPEO_FILTROS["Médicos (Excluyentes)"].keys()))
with col_f2:
    f_pre = st.multiselect("Preferencias Alimentarias", list(MAPEO_FILTROS["Preferencias"].keys()))
with col_f3:
    f_log = st.multiselect("Logística", list(MAPEO_FILTROS["Logística"].keys()))

kcal_obj = st.number_input("Calorías Objetivo Diarias", value=kcal_sugeridas)

# --- 5. CARGA DE DATOS ---
try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    # USAMOS .get() PARA EVITAR EL ERROR SI FALTA UNA CLAVE
    listado_des = db.get('desayunos', [])
    listado_com = db.get('comidas', [])
    listado_col = db.get('colaciones', [])

    # Tags base
    tags_base = [MAPEO_FILTROS["Médicos (Excluyentes)"][f] for f in f_med] + \
                 [MAPEO_FILTROS["Preferencias"][f] for f in f_pre]
    
    # Filtrado inicial
    p_des = filtrar_platos(listado_des, tags_base)
    p_com_full = filtrar_platos(listado_com, tags_base)
    p_col = filtrar_platos(listado_col, tags_base)

    tag_at = [MAPEO_FILTROS["Logística"]["Almuerzo en Trabajo"]]
    almuerzo_trabajo = "Almuerzo en Trabajo" in f_log

    if st.button("🚀 Generar Plan Semanal"):
        if not p_des or not p_com_full:
            st.error("No hay suficientes platos que cumplan los filtros médicos/preferencias.")
        else:
            plan = {}
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            
            for dia in dias:
                mejor_opcion = None
                min_err = 9999
                
                # Almuerzo específico
                opciones_almuerzo = filtrar_platos(p_com_full, tag_at) if almuerzo_trabajo else p_com_full
                if not opciones_almuerzo: opciones_almuerzo = p_com_full # Fallback si no hay AT

                for _ in range(500):
                    d = random.choice(p_des)
                    a = random.choice(opciones_almuerzo)
                    m = random.choice(p_des)
                    c = random.choice(p_com_full)
                    c1 = random.choice(p_col) if (usar_colaciones and p_col) else {"nombre": "-", "kcal": 0}
                    c2 = random.choice(p_col) if (usar_colaciones and p_col) else {"nombre": "-", "kcal": 0}
                    
                    total = d['kcal'] + a['kcal'] + m['kcal'] + c['kcal'] + c1['kcal'] + c2['kcal']
                    if abs(total - kcal_obj) < min_err:
                        min_err = abs(total - kcal_obj)
                        mejor_opcion = {"D": d, "C1": c1, "A": a, "M": m, "C2": c2, "C": c, "Total": total}
                plan[dia] = mejor_opcion
            st.session_state['plan'] = plan

    # --- 6. VISUALIZACIÓN ---
    if 'plan' in st.session_state:
        plan = st.session_state['plan']
        st.markdown("---")
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
