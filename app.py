import streamlit as st
import pandas as pd
import json
import random

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

# --- SECCIÓN DE MACROS EN SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.header("📊 Distribución de Macros")
p_prot = st.sidebar.slider("% Proteína", 10, 50, 20)
p_gras = st.sidebar.slider("% Grasas", 10, 50, 30)
p_carb = 100 - p_prot - p_gras
st.sidebar.info(f"Carbohidratos: {p_carb}%")

# --- SECCIÓN DE FILTROS EN SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.header("🏥 Filtros Especiales")
patologia_map = {
    "Diabetes (db)": "db",
    "Sin TACC (gf)": "gf",
    "Bajo Sodio (ls)": "ls",
    "Vegano (vgn)": "vgn",
    "Vegetariano (veg)": "veg",
    "Almuerzo para Tupper (tp)": "tp"
}
seleccion_filtros = st.sidebar.multiselect("Requerimientos:", options=list(patologia_map.keys()))

# --- 2. CÁLCULOS DE OBJETIVO ---
act_mult = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Intenso": 1.725}
tmb = (10 * peso) + (6.25 * talla) - (5 * edad) + (5 if sexo == "Masculino" else -161)
kcal_base = int(tmb * act_mult[actividad])

# --- 3. CUERPO PRINCIPAL ---
st.title(f"Plan Nutricional: {nombre}")

# Calorías objetivo editables en el centro
kcal_final = st.number_input("Calorías Objetivo Diarias", value=kcal_base)
margen = kcal_final * 0.05 

# Mostrar los gramos resultantes de los macros seleccionados en el sidebar
g_prot = (kcal_final * (p_prot/100)) / 4
g_gras = (kcal_final * (p_gras/100)) / 9
g_carb = (kcal_final * (p_carb/100)) / 4

st.write(f"**Objetivo en gramos:** Proteínas: {int(g_prot)}g | Grasas: {int(g_gras)}g | Carbohidratos: {int(g_carb)}g")

# --- 4. LÓGICA DE CARGA Y FILTRADO ---
try:
    with open('./data/platos.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    tags_activos = [patologia_map[f] for f in seleccion_filtros]

    def filtrar(lista, tags):
        return [p for p in lista if all(t in p.get('tags', []) for t in tags)]

    # Filtramos las listas según los tags
    desayunos_f = filtrar(raw_data.get("desayunos", []), [t for t in tags_activos if t != "tp"])
    comidas_f = filtrar(raw_data.get("comidas", []), tags_activos)

    st.markdown("---")
    st.header("📅 Menú Semanal Optimizado (Margen 5%)")

    if st.button("🚀 Calcular Menú Balanceado"):
        if not desayunos_f or not comidas_f:
            st.warning("No hay platos suficientes con esos filtros.")
        else:
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            cols = st.columns(7)
            
            for i, dia in enumerate(dias):
                with cols[i]:
                    st.subheader(dia)
                    encontrado = False
                    
                    # Intentos de optimización
                    for _ in range(1000): # Aumentamos a 1000 intentos para mayor precisión
                        d = random.choice(desayunos_f)
                        a = random.choice(comidas_f)
                        m = random.choice(desayunos_f)
                        c = random.choice(comidas_f)
                        
                        total = d['kcal'] + a['kcal'] + m['kcal'] + c['kcal']
                        
                        if abs(total - kcal_final) <= margen:
                            st.info(f"**D:** {d['nombre']}")
                            st.success(f"**A:** {a['nombre']} 🍱" if "tp" in a.get('tags',[]) else f"**A:** {a['nombre']}")
                            st.info(f"**M:** {m['nombre']}")
                            st.success(f"**C:** {c['nombre']}")
                            st.metric("Total", f"{total}", f"{int(total-kcal_final)} kcal")
                            encontrado = True
                            break
                    
                    if not encontrado:
                        st.error("Sin éxito ❌")

except Exception as e:
    st.error(f"Error: {e}")
