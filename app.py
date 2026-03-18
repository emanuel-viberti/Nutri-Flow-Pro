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
peso = st.sidebar.number_input("Peso (kg)", value=77.0)
talla = st.sidebar.number_input("Talla (cm)", value=170)
edad = st.sidebar.number_input("Edad", value=30)
actividad = st.sidebar.selectbox("Actividad Física", ["Sedentario", "Ligero", "Moderado", "Intenso"])

# --- CÁLCULOS ANTROPOMÉTRICOS ---
# 1. IMC y Diagnóstico
imc = peso / ((talla/100) ** 2)
if imc < 18.5: diag = "Bajo Peso"
elif 18.5 <= imc < 25: diag = "Normopeso"
elif 25 <= imc < 30: diag = "Sobrepeso"
else: diag = "Obesidad"

# 2. Peso Ideal (Broca: Talla en cm - 100/105)
pi_broca = talla - 100 if sexo == "Masculino" else talla - 105

# Mostrar info en Sidebar
st.sidebar.markdown("---")
st.sidebar.metric("IMC", f"{imc:.1f}", diag)
st.sidebar.metric("Peso Ideal (Broca)", f"{pi_broca} kg")

# --- SECCIÓN DE MACROS (Lógica corregida) ---
st.sidebar.markdown("---")
st.sidebar.header("📊 Distribución de Macros")
p_prot = st.sidebar.slider("% Proteína", 10, 50, 20, step=5)
p_gras = st.sidebar.slider("% Grasas", 10, 50, 30, step=5)

# Carbos se editan AUTOMÁTICAMENTE al mover los otros dos
p_carb = 100 - p_prot - p_gras
st.sidebar.info(f"**Carbohidratos (Auto): {p_carb}%**")

if p_carb < 10:
    st.sidebar.warning("⚠️ Carbohidratos muy bajos.")

# Gráfico de Torta
df_pie = pd.DataFrame({"Macro": ["P", "G", "C"], "Valor": [p_prot, p_gras, p_carb]})
fig = px.pie(df_pie, values='Valor', names='Macro', hole=0.4, height=200)
fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
st.sidebar.plotly_chart(fig, use_container_width=True)

# --- 2. CÁLCULOS DE ENERGÍA ---
act_mult = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
tmb = (10 * peso) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_base = int(tmb * act_mult[actividad])

# --- 3. CUERPO PRINCIPAL ---
st.title(f"Plan Nutricional: {nombre}")

col1, col2 = st.columns(2)
with col1:
    kcal_final = st.number_input("Calorías Objetivo Diarias", value=kcal_base)
with col2:
    st.write(f"**Distribución en Gramos:**")
    st.write(f"P: {int((kcal_final*p_prot/100)/4)}g | G: {int((kcal_final*p_gras/100)/9)}g | C: {int((kcal_final*p_carb/100)/4)}g")

# --- 4. FILTROS Y MENÚ ---
st.sidebar.markdown("---")
patologia_map = {"Diabetes (db)": "db", "Sin TACC (gf)": "gf", "Bajo Sodio (ls)": "ls", 
                 "Vegano (vgn)": "vgn", "Vegetariano (veg)": "veg", "Tupper (tp)": "tp"}
seleccion = st.sidebar.multiselect("Filtros Médicos:", options=list(patologia_map.keys()))

try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    tags = [patologia_map[s] for s in seleccion]
    def filtrar(l, t): return [p for p in l if all(x in p.get('tags', []) for x in t)]
    
    des_f = filtrar(raw['desayunos'], [x for x in tags if x != "tp"])
    com_f = filtrar(raw['comidas'], tags)

    if st.button("🚀 Generar Menú"):
        cols = st.columns(7)
        dias = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
        margen = kcal_final * 0.05

        for i, dia in enumerate(dias):
            with cols[i]:
                st.subheader(dia)
                mejor = None
                m_dif = float('inf')
                
                for _ in range(2000):
                    d, a, m, c = random.choice(des_f), random.choice(com_f), random.choice(des_f), random.choice(com_f)
                    total = d['kcal'] + a['kcal'] + m['kcal'] + c['kcal']
                    dif = abs(total - kcal_final)
                    if dif < m_dif:
                        m_dif, mejor = dif, (d, a, m, c, total)
                    if dif <= margen: break
                
                rd, ra, rm, rc, rt = mejor
                st.caption(f"D: {rd['nombre']}")
                st.success(f"A: {ra['nombre']}")
                st.caption(f"M: {rm['nombre']}")
                st.success(f"C: {rc['nombre']}")
                st.metric("Total", f"{rt}", f"{rt-kcal_final}")

except Exception as e:
    st.error(f"Faltan datos o error en JSON: {e}")
