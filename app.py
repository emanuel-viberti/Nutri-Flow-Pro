import streamlit as st
import pandas as pd
import json
import random

# Configuración de página
st.set_page_config(page_title="Nutri-Flow Pro", layout="wide")

# --- 1. ENTRADA DE DATOS (Sidebar) ---
st.sidebar.header("📋 Datos del Paciente")
nombre = st.sidebar.text_input("Nombre", value="Paciente Ejemplo")
sexo = st.sidebar.selectbox("Sexo", ["Femenino", "Masculino"])
peso = st.sidebar.number_input("Peso (kg)", value=70.0)
talla = st.sidebar.number_input("Talla (cm)", value=170)
edad = st.sidebar.number_input("Edad", value=30)

# AF desplegable hacia abajo (selectbox)
actividad = st.sidebar.selectbox(
    "Nivel de Actividad Física", 
    options=["Sedentario", "Ligero", "Moderado", "Intenso"],
    help="Sedentario (x1.2), Ligero (x1.375), Moderado (x1.55), Intenso (x1.725)"
)

# Cálculos automáticos
act_mult = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
tmb = (10 * peso) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_base = int(tmb * act_mult[actividad])

# --- 2. INTERFAZ PRINCIPAL ---
st.title(f"Plan Nutricional: {nombre}")

col_k, col_p = st.columns(2)
with col_k:
    kcal_final = st.number_input("Calorías Objetivo (Kcal)", value=kcal_base)
with col_p:
    pi_base = talla - 105 if sexo == "Femenino" else talla - 100
    peso_ideal = st.sidebar.number_input("Peso Ideal (kg)", value=float(pi_base))

# --- 3. MACROS EDITABLES ---
st.subheader("📊 Distribución de Macronutrientes")
cm1, cm2, cm3 = st.columns(3)
with cm1:
    p_prot = st.slider("% Proteína", 10, 50, 20)
with cm2:
    p_gras = st.slider("% Grasas", 10, 50, 30)
with cm3:
    p_carb = 100 - p_prot - p_gras
    st.metric("Carbohidratos (Resto)", f"{p_carb}%")

# --- 4. CARGA DE DATOS ---
try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    desayunos_list = raw_data.get("desayunos", [])
    comidas_list = raw_data.get("comidas", [])
    
    st.markdown("---")
    
    # --- 5. GENERADOR DE MENÚ SEMANAL (DAMyC) ---
    st.header("📅 Menú Semanal Sugerido")
    
    if st.button("🚀 Generar Nuevo Menú"):
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        # Creamos columnas para que el menú se vea como una agenda
        cols_menu = st.columns(7)
        
        for i, dia in enumerate(dias):
            with cols_menu[i]:
                st.subheader(dia)
                
                # Seleccionamos platos al azar de tu lista de 500
                d = random.choice(desayunos_list)['nombre'] if desayunos_list else "Sin datos"
                a = random.choice(comidas_list)['nombre'] if comidas_list else "Sin datos"
                m = random.choice(desayunos_list)['nombre'] if desayunos_list else "Sin datos"
                c = random.choice(comidas_list)['nombre'] if comidas_list else "Sin datos"
                
                st.info(f"**D:** {d}")
                st.success(f"**A:** {a}")
                st.info(f"**M:** {m}")
                st.success(f"**C:** {c}")
    else:
        st.write("Hacé clic en el botón para armar la semana.")

except Exception as e:
    st.error(f"Error al procesar el JSON: {e}")
