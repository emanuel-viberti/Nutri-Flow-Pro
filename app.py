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
actividad = st.sidebar.selectbox("Nivel de Actividad Física", 
                                options=["Sedentario", "Ligero", "Moderado", "Intenso"])

# --- NUEVO: FILTRO DE PATOLOGÍAS ---
st.sidebar.header("🏥 Restricciones Médicas")
# Mapeamos lo que elige el usuario con los tags de tu JSON
patologia_map = {
    "Ninguna": None,
    "Diabetes (db)": "db",
    "Sin TACC (gf)": "gf",
    "Bajo Sodio (ls)": "ls",
    "Vegano (vgn)": "vgn"
}
seleccion_patologia = st.sidebar.multiselect("Seleccionar Patologías", options=list(patologia_map.keys()), default=["Ninguna"])

# --- 2. CÁLCULOS ---
act_mult = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
tmb = (10 * peso) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_base = int(tmb * act_mult[actividad])

st.title(f"Plan Nutricional: {nombre}")

col_k, col_p = st.columns(2)
with col_k:
    kcal_final = st.number_input("Calorías Objetivo (Kcal)", value=kcal_base)
with col_p:
    pi_base = talla - 105 if sexo == "Femenino" else talla - 100
    peso_ideal = st.sidebar.number_input("Peso Ideal (kg)", value=float(pi_base))

# --- 3. CARGA Y FILTRADO INTELIGENTE ---
try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Listas originales
    todos_desayunos = raw_data.get("desayunos", [])
    todas_comidas = raw_data.get("comidas", [])

    # APLICAR FILTRO POR TAGS
    tags_a_filtrar = [patologia_map[p] for p in seleccion_patologia if patologia_map[p] is not None]

    def filtrar_por_tags(lista_platos, tags):
        if not tags: return lista_platos
        # Solo dejamos platos que tengan TODOS los tags seleccionados
        return [p for p in lista_platos if all(t in p.get('tags', []) for t in tags)]

    desayunos_aptos = filtrar_por_tags(todos_desayunos, tags_a_filtrar)
    comidas_aptas = filtrar_por_tags(todas_comidas, tags_a_filtrar)

    st.markdown("---")
    
    # --- 4. GENERADOR DE MENÚ SEMANAL ---
    st.header("📅 Menú Semanal Inteligente")
    
    if not desayunos_aptos or not comidas_aptas:
        st.error("⚠️ No hay suficientes platos en la base de datos que cumplan con TODAS las patologías seleccionadas.")
    else:
        if st.button("🚀 Generar Menú Validado"):
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            cols_menu = st.columns(7)
            
            for i, dia in enumerate(dias):
                with cols_menu[i]:
                    st.subheader(dia)
                    
                    # Selección aleatoria de la lista ya filtrada por patología
                    d = random.choice(desayunos_aptos)
                    a = random.choice(comidas_aptas)
                    m = random.choice(desayunos_aptos)
                    c = random.choice(comidas_aptas)
                    
                    # Mostrar nombre y kcal de cada uno
                    st.info(f"**D:** {d['nombre']} ({d['kcal']} kcal)")
                    st.success(f"**A:** {a['nombre']} ({a['kcal']} kcal)")
                    st.info(f"**M:** {m['nombre']} ({m['kcal']} kcal)")
                    st.success(f"**C:** {c['nombre']} ({c['kcal']} kcal)")
                    
                    # Cálculo de kcal totales del día
                    total_dia = d['kcal'] + a['kcal'] + m['kcal'] + c['kcal']
                    st.metric("Total Kcal", f"{total_dia}")

except Exception as e:
    st.error(f"Error: {e}")
