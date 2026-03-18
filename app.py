import streamlit as st
import pandas as pd
import json

# Configuración básica
st.set_page_config(page_title="NutriApp Pro", layout="wide")

# 1. ENTRADA DE DATOS (Sidebar)
st.sidebar.header("📋 Datos del Paciente")
nombre = st.sidebar.text_input("Nombre")
sexo = st.sidebar.selectbox("Sexo", ["Femenino", "Masculino"])
peso = st.sidebar.number_input("Peso (kg)", value=70.0)
talla = st.sidebar.number_input("Talla (cm)", value=170)
edad = st.sidebar.number_input("Edad", value=30)
actividad = st.sidebar.select_slider("Actividad Física", options=["Sedentario", "Ligero", "Moderado", "Intenso"])

# 2. CÁLCULOS (Lógica)
# Peso Ideal (Editable)
pi_sugerido = talla - 105 if sexo == "Femenino" else talla - 100
peso_ideal = st.sidebar.number_input("Peso Ideal (Editable)", value=float(pi_sugerido))

# Kcal (Mifflin-St Jeor)
act_mult = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
tmb = (10 * peso) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_obj = int(tmb * act_mult[actividad])

# 3. INTERFAZ PRINCIPAL
st.title(f"Plan Nutricional: {nombre}")

col1, col2 = st.columns(2)
with col1:
    kcal_final = st.number_input("Calorías Objetivo", value=kcal_obj)
with col2:
    st.write(f"**Peso Ideal:** {peso_ideal} kg")

# Distribución de Macros
st.subheader("Distribución de Macronutrientes")
c1, c2, c3 = st.columns(3)
p_prot = c1.slider("% Proteína", 10, 40, 20)
p_gras = c2.slider("% Grasas", 10, 40, 30)
p_carb = 100 - p_prot - p_gras
c3.metric("Carbohidratos", f"{p_carb}%")

# 4. CARGA DE PLATOS Y FILTROS
try:
    with open('data/platos.json', 'r', encoding='utf-8') as f:
        datos_platos = json.load(f)
    df_platos = pd.DataFrame(datos_platos)
    
    st.markdown("---")
    st.subheader("Base de Datos de Platos")
    perfil = st.selectbox("Filtrar por Perfil", ["omnivoro", "vegetariano", "vegano"])
    
    # Mostrar tabla filtrada
    tabla_filtrada = df_platos[df_platos['perfil'] == perfil]
    st.dataframe(tabla_filtrada)

except Exception as e:
    st.error("Primero debés crear el archivo data/platos.json en GitHub")

st.button("Generar Menú Semanal (Próximamente)")
