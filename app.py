import streamlit as st
import pandas as pd
import json

# Configuración de página
st.set_page_config(page_title="Nutri-Flow Pro", layout="wide")

# --- 1. ENTRADA DE DATOS (Sidebar) ---
st.sidebar.header("📋 Datos del Paciente")
nombre = st.sidebar.text_input("Nombre", value="Paciente Ejemplo")
sexo = st.sidebar.selectbox("Sexo", ["Femenino", "Masculino"])
peso = st.sidebar.number_input("Peso (kg)", value=70.0)
talla = st.sidebar.number_input("Talla (cm)", value=170)
edad = st.sidebar.number_input("Edad", value=30)
actividad = st.sidebar.select_slider("Actividad Física", options=["Sedentario", "Ligero", "Moderado", "Intenso"])

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
    peso_ideal = st.number_input("Peso Ideal (kg)", value=float(pi_base))

# --- 3. MACROS EDITABLES (Solución al 50% clavado) ---
st.subheader("📊 Distribución de Macronutrientes")
cm1, cm2, cm3 = st.columns(3)

with cm1:
    p_prot = st.slider("% Proteína", 10, 50, 20)
with cm2:
    p_gras = st.slider("% Grasas", 10, 50, 30)
with cm3:
    # El carbohidrato ahora es el resto, pero se muestra dinámicamente
    p_carb = 100 - p_prot - p_gras
    st.metric("Carbohidratos (Resto)", f"{p_carb}%")

if p_carb < 10:
    st.warning("⚠️ Los carbohidratos son muy bajos. Ajustá Proteína o Grasas.")

# --- 4. CARGA DE DATOS (Solución al error de Length) ---
try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Combinamos desayunos y comidas en una sola lista para la tabla
    lista_total = []
    for plato in raw_data.get("desayunos", []):
        plato["categoria"] = "Desayuno/Merienda"
        lista_total.append(plato)
    for plato in raw_data.get("comidas", []):
        plato["categoria"] = "Almuerzo/Cena"
        lista_total.append(plato)
    
    df_platos = pd.DataFrame(lista_total)
    
    st.markdown("---")
    st.subheader("🥗 Buscador de Platos")
    
    # Filtros
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        cat_sel = st.selectbox("Filtrar por Momento", ["Todos", "Desayuno/Merienda", "Almuerzo/Cena"])
    with c_f2:
        tag_sel = st.text_input("Buscar por Tag (ej: db, gf, vgn)")

    # Lógica de filtrado
    df_filtrado = df_platos.copy()
    if cat_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado['categoria'] == cat_sel]
    if tag_sel:
        df_filtrado = df_filtrado[df_filtrado['tags'].apply(lambda x: tag_sel.lower() in [t.lower() for t in x])]

    st.dataframe(df_filtrado, use_container_width=True)

except Exception as e:
    st.error(f"Error al procesar el JSON: {e}")

st.button("🔄 Generar Menú Semanal")
