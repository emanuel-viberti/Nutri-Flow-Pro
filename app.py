import streamlit as st
import pandas as pd
import json
import random
import plotly.express as px

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

# --- 3. SECCIÓN DE MACROS ---
st.sidebar.markdown("---")
st.sidebar.header("📊 Distribución de Macros")
p_prot = st.sidebar.slider("% Proteína", 10, 50, 20, step=5)
p_gras = st.sidebar.slider("% Grasas", 10, 50, 30, step=5)
p_carb = 100 - p_prot - p_gras # Automático

if p_carb < 0:
    st.sidebar.error("Suma > 100%. Bajá otros macros.")
    p_carb = 0
else:
    st.sidebar.info(f"Carbohidratos: {p_carb}%")

# Gráfico de Torta
df_pie = pd.DataFrame({"Macro": ["Prot", "Gras", "Carb"], "Val": [p_prot, p_gras, p_carb]})
fig = px.pie(df_pie, values='Val', names='Macro', hole=0.4, height=180, color_discrete_sequence=px.colors.qualitative.Safe)
fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
st.sidebar.plotly_chart(fig, use_container_width=True)

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

# --- 5. FILTROS Y MENÚ SEMANAL ---
st.sidebar.markdown("---")
pat_map = {"Diabetes (db)": "db", "Sin TACC (gf)": "gf", "Bajo Sodio (ls)": "ls", 
           "Vegano (vgn)": "vgn", "Vegetariano (veg)": "veg", "Tupper (tp)": "tp"}
seleccion = st.sidebar.multiselect("Filtros Médicos:", options=list(pat_map.keys()))

try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    tags = [pat_map[s] for s in seleccion]
    def filtrar(l, t): return [p for p in l if all(x in p.get('tags', []) for x in t)]
    
    des_f = filtrar(raw['desayunos'], [x for x in tags if x != "tp"])
    com_f = filtrar(raw['comidas'], tags)

    if st.button("🚀 Generar Menú DAMyC"):
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        cols = st.columns(7)
        margen = kcal_final * 0.05

        for i, dia in enumerate(dias):
            with cols[i]:
                st.subheader(dia)
                mejor = None
                m_dif = float('inf')
                
                # Buscador optimizado
                for _ in range(2000):
                    d, a, m, c = random.choice(des_f), random.choice(com_f), random.choice(des_f), random.choice(com_f)
                    total = d['kcal'] + a['kcal'] + m['kcal'] + c['kcal']
                    dif = abs(total - kcal_final)
                    if dif < m_dif:
                        m_dif, mejor = dif, (d, a, m, c, total)
                    if dif <= margen: break
                
                rd, ra, rm, rc, rt = mejor
                st.write(f"**D:** {rd['nombre']}")
                st.success(f"**A:** {ra['nombre']}")
                st.write(f"**M:** {rm['nombre']}")
                st.success(f"**C:** {rc['nombre']}")
                st.metric("Total", f"{rt}", f"{rt-kcal_final} kcal")

except Exception as e:
    st.error(f"Error: {e}. Revisa si tu JSON tiene los tags correctamente.")
