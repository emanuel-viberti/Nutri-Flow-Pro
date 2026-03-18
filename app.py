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

# --- BLOQUE DE MACROS CORREGIDO (EDITABLE) ---
st.subheader("Distribución de Macronutrientes (Editable)")
st.markdown("Ajustá los porcentajes. El total debe ser 100%.")

col_p, col_g, col_c = st.columns(3)

# Usamos sliders independientes para que el nutri pueda clavarlos donde quiera
with col_p:
    p_prot = st.slider("% Proteína", 10, 50, 20, key="prot_slider")
with col_g:
    p_gras = st.slider("% Grasas", 10, 50, 30, key="gras_slider")
with col_c:
    p_carb = st.slider("% Carbohidratos", 10, 70, 50, key="carb_slider")

total_macros = p_prot + p_gras + p_carb

# Validación visual
if total_macros != 100:
    st.error(f"⚠️ La suma de macros es {total_macros}%. Debe ser exactamente 100% para generar el menú.")
else:
    st.success("✅ Distribución de macros correcta (100%).")
    
    # Cálculo de gramos reales (para el futuro algoritmo)
    g_prot = (kcal_final * (p_prot/100)) / 4
    g_gras = (kcal_final * (p_gras/100)) / 9
    g_carb = (kcal_final * (p_carb/100)) / 4
    
    st.write(f"**Gramos:** P: {int(g_prot)}g | G: {int(g_gras)}g | C: {int(g_carb)}g")
# -----------------------------------------------
# 4. CARGA DE PLATOS Y FILTROS
try:
   with open('./data/platos.json', 'r', encoding='utf-8') as f:
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
