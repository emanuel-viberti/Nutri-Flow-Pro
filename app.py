import streamlit as st
import pandas as pd
import json
import random
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. CONFIGURACIÓN Y FUNCIONES ---
st.set_page_config(page_title="Nutri-Flow Pro", layout="wide")

def filtrar_platos(lista, filtros):
    """Filtra platos que contengan TODOS los tags seleccionados."""
    if not filtros:
        return lista
    return [p for p in lista if all(f in p.get('tags', []) for f in filtros)]

def calcular_gramos_macro(kcal_plato, p_prot, p_gras, p_carb):
    """Calcula gramos de macros para una cantidad de kcal específica."""
    g_prot = round((kcal_plato * (p_prot / 100)) / 4, 1)
    g_gras = round((kcal_plato * (p_gras / 100)) / 9, 1)
    g_carb = round((kcal_plato * (p_carb / 100)) / 4, 1)
    return {"p": g_prot, "g": g_gras, "c": g_carb}

def generar_pdf(plan_semanal, nombre_paciente, config_nutri):
    """Crea un documento PDF con el plan y porciones detalladas."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(200, 10, f"Plan Nutricional: {nombre_paciente}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 7, f"Objetivo: {config_nutri['kcal']} kcal | P: {config_nutri['p']}% | G: {config_nutri['g']}% | C: {config_nutri['c']}%", ln=True, align="C")
    pdf.ln(10)

    for dia, comidas in plan_semanal.items():
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 8, f"--- {dia.upper()} ---", ln=True, fill=True, align="C")
        pdf.ln(2)
        
        for tipo, p in comidas.items():
            if p and isinstance(p, dict) and "nombre" in p:
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 6, f"{tipo}: {p['nombre']} ({p['kcal']} kcal)", ln=True)
                
                m = calcular_gramos_macro(p['kcal'], config_nutri['p'], config_nutri['g'], config_nutri['c'])
                pdf.set_font("Arial", "", 9)
                pdf.cell(0, 5, f"   Porcion: Proteina {m['p']}g | Grasa {m['g']}g | Carbohidratos {m['c']}g", ln=True)
                pdf.ln(1)
        pdf.ln(3)
        
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 2. SIDEBAR (ENTRADA DE DATOS) ---
st.sidebar.header("📋 Perfil del Paciente")
nombre = st.sidebar.text_input("Nombre", value="Paciente")
peso_actual = st.sidebar.number_input("Peso (kg)", value=70.0)
talla = st.sidebar.number_input("Talla (cm)", value=170)
edad = st.sidebar.number_input("Edad", value=30)
sexo = st.sidebar.selectbox("Sexo", ["Masculino", "Femenino"])
actividad = st.sidebar.selectbox("Actividad", ["Sedentario", "Ligero", "Moderado", "Intenso"])

# Cálculo de Gasto Calórico (Mifflin-St Jeor)
act_mult = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
tmb = (10 * peso_actual) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_base = int(tmb * act_mult[actividad])

st.sidebar.markdown("---")
st.sidebar.header("📊 Macros")
p_prot = st.sidebar.slider("% Proteina", 10, 50, 25, 5)
p_gras = st.sidebar.slider("% Grasa", 10, 50, 25, 5)
p_carb = 100 - p_prot - p_gras

if p_carb < 0:
    st.sidebar.error("¡Macros exceden 100%!")
    p_carb = 0
else:
    st.sidebar.info(f"Carbohidratos: {p_carb}%")

usar_colaciones = st.sidebar.checkbox("¿Incluir 2 Colaciones?", value=True)

# --- 3. CARGA DE DATOS Y FILTROS ---
try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        raw = json.load(f)

    st.title("🍎 Nutri-Flow Pro")
    
    pat_map = {
        "Diabetes (db)": "db", "Sin TACC (gf)": "gf", 
        "Bajo Sodio (ls)": "ls", "Vegano (vgn)": "vgn", 
        "Tupper (tp)": "tp"
    }
    seleccion = st.multiselect("Filtros Dietarios:", options=list(pat_map.keys()))
    
    tags_sel = [pat_map[s] for s in seleccion]
    # Filtrar listas
    p_des = filtrar_platos(raw['desayunos'], tags_sel)
    p_alm = filtrar_platos(raw['comidas'], tags_sel)
    p_cen = filtrar_platos(raw['comidas'], tags_sel)
    p_col = filtrar_platos(raw.get('colaciones', []), tags_sel)

    # Monitor de disponibilidad
    with st.expander("🔍 Disponibilidad de platos"):
        st.write(f"Desayunos: {len(p_des)} | Almuerzos: {len(p_alm)} | Colaciones: {len(p_col)}")

    kcal_final = st.number_input("Calorias Objetivo", value=kcal_base)

    # --- 4. GENERACIÓN DEL PLAN ---
    if st.button("🚀 Generar Plan Semanal"):
        if not p_des or not p_alm:
            st.error("No hay suficientes platos para esos filtros.")
        else:
            plan_semana = {}
            dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
            
            for dia in dias:
                mejor_opcion = None
                min_dif = float('inf')
                
                # Algoritmo de aproximación
                for _ in range(1000):
                    d = random.choice(p_des)
                    a = random.choice(p_alm)
                    m = random.choice(p_des)
                    c = random.choice(p_cen)
                    c1 = random.choice(p_col) if (usar_colaciones and p_col) else {"nombre": "-", "kcal": 0}
                    c2 = random.choice(p_col) if (usar_colaciones and p_col) else {"nombre": "-", "kcal": 0}
                    
                    total_kcal = d['kcal'] + a['kcal'] + m['kcal'] + c['kcal'] + c1['kcal'] + c2['kcal']
                    dif = abs(total_kcal - kcal_final)
                    
                    if dif < min_dif:
                        min_dif = dif
                        mejor_opcion = {
                            "Desayuno": d, "C1": c1, "Almuerzo": a, 
                            "Merienda": m, "C2": c2, "Cena": c, "Total": total_kcal
                        }
                    if dif < 50: break # Margen aceptable
                
                plan_semana[dia] = mejor_opcion

            st.session_state['plan_activo'] = plan_semana
            st.session_state['config_actual'] = {"kcal": kcal_final, "p": p_prot, "g": p_gras, "c": p_carb}

    # --- 5. VISUALIZACIÓN Y DESCARGA ---
    if 'plan_activo' in st.session_state:
        st.markdown("---")
        plan = st.session_state['plan_activo']
        cols = st.columns(7)
        
        for i, (dia, comps) in enumerate(plan.items()):
            with cols[i]:
                st.subheader(dia)
                st.caption(f"Total: {comps['Total']} kcal")
                st.write(f"**D:** {comps['Desayuno']['nombre']}")
                if usar_colaciones: st.write(f"**C1:** {comps['C1']['nombre']}")
                st.success(f"**A:** {comps['Almuerzo']['nombre']}")
                st.write(f"**M:** {comps['Merienda']['nombre']}")
                if usar_colaciones: st.write(f"**C2:** {comps['C2']['nombre']}")
                st.success(f"**C:** {comps['Cena']['nombre']}")

        st.markdown("---")
        pdf_bytes = generar_pdf(plan, nombre, st.session_state['config_actual'])
        st.download_button(
            label="📥 Descargar PDF para el Paciente",
            data=pdf_bytes,
            file_name=f"Plan_{nombre}.pdf",
            mime="application/pdf"
        )

except Exception as e:
    st.error(f"Error cargando la aplicación: {e}")
    st.info("Asegurate de que './data/platos.json' exista y tenga el formato correcto.")
