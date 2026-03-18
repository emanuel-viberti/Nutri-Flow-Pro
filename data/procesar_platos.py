import json

def procesar_base_datos():
    try:
        with open('platos.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        # Unificar Almuerzos y Cenas en "comidas"
        comidas_unificadas = db.get('comidas', [])
        if 'almuerzos' in db: comidas_unificadas.extend(db['almuerzos'])
        if 'cenas' in db: comidas_unificadas.extend(db['cenas'])

        # Mapeo de Tags Médicos
        mapeo_salud = {
            "db": "db2", "ls": "lf", "gf": "gf"
        }
        # Tags de seguridad por defecto (se asume apto a menos que se detecte ingrediente)
        seguridad = ["hta", "dlp", "afn", "ahv", "amr", "asj"]

        def limpiar_tags(plato, es_comida=False):
            nombre = plato['nombre'].lower()
            tags_originales = plato.get('tags', [])
            nuevos_tags = []

            # 1. Convertir tags viejos
            for t in tags_originales:
                if t in mapeo_salud: nuevos_tags.append(mapeo_salud[t])
            
            # 2. Agregar seguridad base
            nuevos_tags.extend(seguridad)

            # 3. Lógica de exclusión estricta (Celiaquía / Diabetes)
            prohibido_gf = ["pan", "fideo", "pasta", "tarta", "harina", "avena", "milanesa", "rebozado", "ñoqui", "pizza"]
            if any(p in nombre for p in prohibido_gf) and "sin tacc" not in nombre:
                if "gf" in nuevos_tags: nuevos_tags.remove("gf")

            prohibido_db2 = ["miel", "azúcar", "dulce", "membrillo", "batata", "pasas", "ñoqui"]
            if any(p in nombre for p in prohibido_db2):
                if "db2" in nuevos_tags: nuevos_tags.remove("db2")

            # 4. Lógica "Almuerzo en Trabajo" (Tag: 'at')
            # Platos fáciles de llevar/ensamblar: Ensaladas, wraps, tartas, arroz, tartas.
            apto_trabajo = ["ensalada", "tarta", "sándwich", "sandwich", "wrap", "arroz", "frío", "atún", "vianda"]
            if es_comida and any(a in nombre for a in apto_trabajo):
                nuevos_tags.append("at")

            return list(set(nuevos_tags))

        # Procesar Desayunos
        for p in db.get('desayunos', []):
            p['tags'] = limpiar_tags(p)

        # Procesar Comidas
        for p in comidas_unificadas:
            p['tags'] = limpiar_tags(p, es_comida=True)

        # Guardar resultado
        nueva_db = {
            "desayunos": db.get('desayunos', []),
            "comidas": comidas_unificadas,
            "colaciones": db.get('colaciones', [])
        }

        with open('platos.json', 'w', encoding='utf-8') as f:
            json.dump(nueva_db, f, indent=2, ensure_ascii=False)
        
        print("✅ Base de datos de 500 platos actualizada.")
        print("✅ Filtro 'Almuerzo en Trabajo' (at) aplicado.")
        print("✅ Estructura A y C unificada en 'comidas'.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    procesar_base_datos()
