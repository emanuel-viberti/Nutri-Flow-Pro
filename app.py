import streamlit as st
import pandas as pd
import json
import random
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Nutri-Flow Pro", layout="wide")

# --- FUNCIONES DE APOYO ---
def filtrar_platos(lista, filtros):
    if not filtros:
        return lista
    # Filtra solo si el plato tiene TODOS los tags seleccionados
    platos_filtrados = [p for p in lista if all(f in p.get('tags', []) for f in filtros)]
    return platos_filtrados

def calcular_gramos_macro(kcal_plato, p_prot, p_gras, p_carb):
    """Calcula gramos exactos de macros para una cantidad de kcal específica"""
    g_prot = round((kcal_plato * (p_prot / 100)) / 4, 1)
    g_gras = round((kcal_plato * (p_gras / 100)) / 9, 1)
    g_carb = round((kcal_plato * (p_carb / 100)) / 4, 1)
    return {"p": g_prot, "g": g_gras, "c": g_carb}

# --- MONITOR DE FILTROS ---
with st.expander("🔍 Verificar disponibilidad de platos con filtros actuales"):
    st.write(f"🍞 Desayunos/Meriendas: {len(p_des)} disponibles")
    st.write(f"🍱 Almuerzos: {len(p_alm)} disponibles")
    st.write(f"🌙 Cenas: {len(p_cen)} disponibles")
    st.write(f"🍎 Colaciones: {len(p_col)} disponibles")
    
    if len(p_des) == 0 or len(p_alm) == 0:
        st.error("⚠️ ¡OJO! Con estos filtros no hay platos suficientes. El generador va a fallar.")

def generar_pdf(plan_semanal, nombre_paciente, config_nutri):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Encabezado
    pdf.cell(200, 10, f"Plan Nutricional Personalizado: {nombre_paciente}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 7, f"Objetivo Diario: {config_nutri['kcal']} kcal | P: {config_nutri['p']}% | G: {config_nutri['g']}% | C: {config_nutri['c']}%", ln=True, align="C")
    pdf.ln(10)

    for dia, comidas in plan_semanal.items():
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 8, f"--- {dia.upper()} ---", ln=True, fill=True, align="C")
        pdf.ln(2)
        
        for tipo, p in comidas.items():
            if p:
                # Nombre del plato
                pdf.set_font("Arial", "B", 11)
                pdf.cell(0, 6, f"{tipo}: {p['nombre']} ({p['kcal']} kcal)", ln=True)
                
                # Cálculo de porción dinámica para el PDF
                m = calcular_gramos_macro(p['kcal'], config_nutri['p'], config_nutri['g'], config_nutri['c'])
                pdf.set_font("Arial", "", 10)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(0, 5, f"   > Porción: Proteínas {m['p']}g | Grasas {m['g']}g | Carbohidratos {m['c']}g", ln=True)
                
                # Receta/Instrucción
                pdf.set_font("Arial", "I", 9)
                receta = p.get('receta', 'Consultar preparación según guía de macros.')
                pdf.multi_cell(0, 5, f"   Instrucción: {receta}")
                pdf.ln(2)
        pdf.ln(4)
        
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- SIDEBAR: DATOS Y PARÁMETROS ---
st.sidebar.header("📋 Perfil del Paciente")
nombre = st.sidebar.text_input("Nombre completo", value="Paciente Ejemplo")
sexo = st.sidebar.selectbox("Sexo", ["Femenino", "Masculino"])
peso_actual = st.sidebar.number_input("Peso Actual (kg)", value=77.0)
talla = st.sidebar.number_input("Talla (cm)", value=170)
edad = st.sidebar.number_input("Edad", value=30)
actividad = st.sidebar.selectbox("Actividad Física", ["Sedentario", "Ligero", "Moderado", "Intenso"])

# IMC Dinámico
imc = peso_actual / ((talla/100) ** 2)
color_imc = "normal" if 18.5 <= imc < 25 else "inverse"
st.sidebar.metric("IMC Actual", f"{imc:.1f}", delta_color=color_imc)

# Peso Ideal Editable
pi_sugerido = talla - 100 if sexo == "Masculino" else talla - 105
peso_ideal = st.sidebar.number_input("Peso Ideal Objetivo (kg)", value=float(pi_sugerido), help="Base: Fórmula de Broca")

# Cálculo de Kcal basado en Peso Ideal
act_mult = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
tmb_pi = (10 * peso_ideal) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_recomendadas = int(tmb_pi * act_mult[actividad])

st.sidebar.markdown("---")
st.sidebar.header("📊 Configuración de Dieta")
p_prot = st.sidebar.slider("% Proteína", 10, 50, 20, step=5)
p_gras = st.sidebar.slider("% Grasas", 10, 50, 30, step=5)
p_carb = 100 - p_prot - p_gras

if p_carb < 0:
    st.sidebar.error("Suma de macros > 100%")
    p_carb = 0
else:
    st.sidebar.info(f"Carbohidratos: {p_carb}%")

usar_colaciones = st.sidebar.checkbox("Incluir 2 Colaciones (Plan 6 comidas)", value=True)

# --- MAIN: INTERFAZ PRINCIPAL ---
st.title(f"Gestor Nutricional DAMyC")
col_cal1, col_cal2 = st.columns(2)

with col_cal1:
    kcal_final = st.number_input("Calorías Objetivo Diarias", value=kcal_recomendadas)
    st.caption(f"💡 Sugerencia según Peso Ideal: {kcal_recomendadas} kcal")

with col_cal2:
    g_totales = calcular_gramos_macro(kcal_final, p_prot, p_gras, p_carb)
    st.info(f"Totales Diarios: P: {g_totales['p']}g | G: {g_totales['g']}g | C: {g_totales['c']}g")

# --- CARGA Y FILTRADO ---
pat_map = {"Diabetes (db)": "db", "Sin TACC (gf)": "gf", "Bajo Sodio (ls)": "ls", 
           "Vegano (vgn)": "vgn", "Vegetariano (veg)": "veg", "Tupper (tp)": "tp"}
seleccion = st.multiselect("Filtros Médicos / Logísticos:", options=list(pat_map.keys()))

try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    tags_sel = [pat_map[s] for s in seleccion]
    es_tp = "tp" in tags_sel
    t_med = [t for t in tags_sel if t != "tp"]

    p_des = filtrar_platos(raw['desayunos'], t_med)
    p_alm = filtrar_platos(raw['comidas'], t_med + (["tp"] if es_tp else []))
    p_cen = filtrar_platos(raw['comidas'], t_med)
    p_col = filtrar_platos(raw.get('colaciones', []), t_med)

    if st.button("🚀 Generar Nuevo Menú Semanal"):
        plan_temp = {}
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        margen = kcal_final * 0.05

        for dia in dias:
            mejor_dia = None
            min_dif = float('inf')

            for _ in range(2000):
                d, a, m, c = random.choice(p_des), random.choice(p_alm), random.choice(p_des), random.choice(p_cen)
                c1 = random.choice(p_col) if (usar_colaciones and p_col) else None
                c2 = random.choice(p_col) if (usar_colaciones and p_col) else None
                
                total = d['kcal'] + a['kcal'] + m['kcal'] + c['kcal']
                if c1: total += c1['kcal'] + c2['kcal']
                
                dif = abs(total - kcal_final)
                if dif < min_dif:
                    min_dif = dif
                    mejor_dia = {"Desayuno": d, "C1": c1, "Almuerzo": a, "Merienda": m, "C2": c2, "Cena": c, "Total": total}
                if dif <= margen: break
            
            plan_temp[dia] = mejor_dia

        st.session_state['plan_activo'] = plan_temp
        st.session_state['config_pdf'] = {'kcal': kcal_final, 'p': p_prot, 'g': p_gras, 'c': p_carb}

    # --- MOSTRAR MENÚ EN PANTALLA ---
    if 'plan_activo' in st.session_state:
        st.markdown("---")
        cols_pantalla = st.columns(7)
        plan = st.session_state['plan_activo']
        
        for idx, (dia, comidas) in enumerate(plan.items()):
            with cols_pantalla[idx]:
                st.subheader(dia)
                st.write(f"**D:** {comidas['Desayuno']['nombre']}")
                if comidas['C1']: st.caption(f"🔸C1: {comidas['C1']['nombre']}")
                st.success(f"**A:** {comidas['Almuerzo']['nombre']}")
                st.write(f"**M:** {comidas['Merienda']['nombre']}")
                if comidas['C2']: st.caption(f"🔸C2: {comidas['C2']['nombre']}")
                st.success(f"**C:** {comidas['Cena']['nombre']}")
                st.metric("Kcal", f"{comidas['Total']}")

        # --- BOTÓN DE DESCARGA PDF ---
        pdf_data = generar_pdf(plan, nombre, st.session_state['config_pdf'])
        st.download_button(
            label="📥 Descargar Plan Detallado (PDF)",
            data=pdf_data,
            file_name=f"Plan_{nombre}.pdf",
            mime="application/pdf"
        )

except Exception as e:
    st.error(f"Error: {e}. Revisa la estructura de tu JSON.")
