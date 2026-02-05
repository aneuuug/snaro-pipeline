#!/usr/bin/env python3
"""
Script para convertir el CSV de SABI a formato JavaScript para SNARO Pipeline
"""
import csv
import json
import re

# Leer CSV
input_file = '/Users/aneugartelopez/Desktop/Empresas Euskadi.csv'
output_file = '/Users/aneugartelopez/Snaro/app/Snaro-pipeline/empresas_sabi.js'

companies = []
id_counter = 1

# Mapeo de localidades a provincias
def get_provincia(localidad):
    localidad = localidad.upper()
    bizkaia = ['BILBAO', 'BARAKALDO', 'GETXO', 'PORTUGALETE', 'SANTURTZI', 'BASAURI', 'LEIOA',
               'ERANDIO', 'GALDAKAO', 'DURANGO', 'BERMEO', 'GERNIKA', 'MUNGIA', 'AMOREBIETA',
               'SESTAO', 'DERIO', 'ZAMUDIO', 'SOPELA', 'MUSKIZ', 'ERMUA', 'EIBAR', 'ABANTO']
    gipuzkoa = ['DONOSTIA', 'SAN SEBASTIAN', 'IRUN', 'ERRENTERIA', 'ZARAUTZ', 'TOLOSA',
                'ARRASATE', 'MONDRAGON', 'HERNANI', 'EIBAR', 'AZPEITIA', 'AZKOITIA',
                'BEASAIN', 'PASAIA', 'LASARTE', 'ANDOAIN', 'OÑATI', 'BERGARA', 'ELGOIBAR']
    araba = ['VITORIA', 'GASTEIZ', 'LLODIO', 'AMURRIO', 'SALVATIERRA', 'AGURAIN', 'LAGUARDIA']

    for city in bizkaia:
        if city in localidad:
            return 'Bizkaia'
    for city in gipuzkoa:
        if city in localidad:
            return 'Gipuzkoa'
    for city in araba:
        if city in localidad:
            return 'Araba'
    return 'Euskadi'

# Determinar sector basado en nombre de empresa
def get_sector(nombre):
    nombre = nombre.upper()

    if any(x in nombre for x in ['IBERDROLA', 'ENERGIA', 'ELECTRIC', 'SOLAR', 'EOLICA', 'GAS ', 'PETROL']):
        return 'Energía'
    if any(x in nombre for x in ['BANCO', 'KUTXA', 'CAJA', 'SEGUROS', 'INSURANCE', 'FINANCI']):
        return 'Servicios'
    if any(x in nombre for x in ['CONSTRUC', 'INMOBIL', 'PROMOCION', 'EDIFICI']):
        return 'Construcción'
    if any(x in nombre for x in ['HOSPITAL', 'CLINIC', 'FARMA', 'MEDIC', 'SALUD', 'SANITAR']):
        return 'Salud'
    if any(x in nombre for x in ['TECNOLOG', 'SOFTWARE', 'INFORMAT', 'DIGITAL', 'DATA', 'SYSTEM', 'CONSULT']):
        return 'Tecnología'
    if any(x in nombre for x in ['TRANSPORT', 'LOGISTIC', 'ALMACEN', 'DISTRIBU']):
        return 'Logística'
    if any(x in nombre for x in ['ALIMENT', 'BEBIDA', 'CAFE', 'RESTAUR', 'HOTEL', 'CATERING']):
        return 'Alimentación'
    if any(x in nombre for x in ['AUTOMOV', 'AUTOMOTIVE', 'MOTOR', 'VEHIC', 'NEUMAT', 'RECAMB']):
        return 'Automoción'
    if any(x in nombre for x in ['INDUSTR', 'FABRIC', 'MANUFACT', 'MAQUIN', 'METALUR', 'ACERO', 'FUNDIC']):
        return 'Industria'
    if any(x in nombre for x in ['COMERCI', 'RETAIL', 'TIENDA', 'VENTA', 'SUPERMERCADO']):
        return 'Distribución'

    return 'Servicios'  # Default

# Determinar prioridad según facturación
def get_priority(ingresos):
    try:
        ing = float(ingresos.replace('.', '').replace(',', '.'))
        if ing > 100000:  # > 100M€
            return 'high'
        elif ing > 10000:  # > 10M€
            return 'high'
        elif ing > 1000:  # > 1M€
            return 'medium'
        else:
            return 'low'
    except:
        return 'medium'

print("Leyendo CSV de SABI...")

with open(input_file, 'r', encoding='utf-8-sig') as f:
    # Saltar las primeras líneas de cabecera (hasta línea 142)
    content = f.read()
    lines = content.split('\n')

    for line in lines[142:]:  # Empezar desde la fila de datos
        if not line.strip():
            continue

        parts = line.split(';')
        if len(parts) < 10:
            continue

        try:
            # Extraer datos relevantes
            nombre = parts[1].strip().replace('"', '')
            if not nombre or nombre == 'Nombre':
                continue

            nif = parts[2].strip() if len(parts) > 2 else ''
            localidad = parts[3].strip() if len(parts) > 3 else ''
            ingresos = parts[7].strip() if len(parts) > 7 else '0'
            empleados = parts[100].strip() if len(parts) > 100 else '0'  # Columna de empleados

            # Limpiar nombre (quitar SOCIEDAD ANONIMA, SL, etc)
            nombre_limpio = nombre
            for suffix in ['SOCIEDAD ANONIMA.', 'SOCIEDAD ANONIMA', 'SOCIEDAD LIMITADA.',
                          'SOCIEDAD LIMITADA', ' S.A.', ' SA.', ' SA', ' SL.', ' SL', ' S.L.']:
                nombre_limpio = nombre_limpio.replace(suffix, '')
            nombre_limpio = nombre_limpio.strip()
            if nombre_limpio.endswith(','):
                nombre_limpio = nombre_limpio[:-1]

            # Crear detalle con info financiera
            try:
                ing_num = float(ingresos.replace('.', '').replace(',', '.'))
                ing_str = f"{ing_num/1000:.0f}M€" if ing_num > 1000 else f"{ing_num:.0f}K€"
            except:
                ing_str = "N/D"

            try:
                emp_num = int(empleados.replace('.', '').replace(',', ''))
                emp_str = f"{emp_num} empleados"
            except:
                emp_str = ""

            detail = f"Facturación: {ing_str}"
            if emp_str:
                detail += f" · {emp_str}"

            company = {
                'id': id_counter,
                'name': nombre_limpio,
                'nif': nif,
                'sector': get_sector(nombre),
                'location': f"{localidad}, {get_provincia(localidad)}",
                'priority': get_priority(ingresos),
                'detail': detail,
                'ingresos': ingresos,
                'empleados': empleados
            }

            companies.append(company)
            id_counter += 1

            if id_counter % 1000 == 0:
                print(f"Procesadas {id_counter} empresas...")

        except Exception as e:
            continue

print(f"\nTotal empresas procesadas: {len(companies)}")

# Generar JavaScript
js_content = f"""// Empresas de SABI - {len(companies)} empresas de Euskadi
// Generado automáticamente desde SABI database

const empresasSABI = [
"""

for c in companies:
    js_content += f"""    {{ id: {c['id']}, name: '{c['name'].replace("'", "\\'")}', sector: '{c['sector']}', location: '{c['location']}', priority: '{c['priority']}', detail: '{c['detail'].replace("'", "\\'")}' }},
"""

js_content += "];\n"

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(js_content)

print(f"Archivo generado: {output_file}")
print("\nEjemplo de empresas:")
for c in companies[:5]:
    print(f"  - {c['name']} ({c['sector']}) - {c['location']}")
