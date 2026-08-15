import os
import pandas as pd
from datetime import datetime

def run_ops_pipeline():
    print(" Ingestionando datos de HubSpot...")
    
    # Obtenemos la ruta absoluta de la carpeta donde está este script (src)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construimos las rutas automáticas hacia data_raw y data_processed
    raw_path = os.path.join(base_dir, "..", "data_raw", "hubspot_leads_raw.csv")
    output_path = os.path.join(base_dir, "..", "data_processed", "hubspot_leads_clean.csv")

    # Verificamos si el archivo existe antes de abrirlo
    if not os.path.exists(raw_path):
        print(f"\n❌ Error: No se encontró el archivo en: {raw_path}")
        print("Revisá que la carpeta 'data_raw' y el archivo 'hubspot_leads_raw.csv' existan y estén bien nombrados.")
        return

    # 1. Cargar el dataset crudo
    df = pd.read_csv(raw_path)

    print(" Limpiando y normalizando campos...")
    # 2. Limpieza de texto
    df['contact_name'] = df['contact_name'].str.strip().str.title()
    df['email'] = df['email'].str.strip().str.lower()
    
    # 3. Tratar campos nulos o vacíos
    df['pipeline_stage'] = df['pipeline_stage'].fillna("Etapa no asignada")
    df['deal_value_usd'] = df['deal_value_usd'].fillna(0)

    print(" Identificando duplicados...")
    # 4. Detectar duplicados por correo electrónico
    df['es_duplicado'] = df.duplicated(subset=['email'], keep='first')

    print(" Calculando métricas de SLA y tiempos de respuesta...")
    # 5. Convertir a formato de fecha y calcular inactividad
    df['last_activity_date'] = pd.to_datetime(df['last_activity_date'])
    today = pd.to_datetime("2026-08-15")
    df['dias_inactivo'] = (today - df['last_activity_date']).dt.days

    # 6. Regla de negocio de Operaciones
    def clasificar_alerta(row):
        if row['pipeline_stage'] == 'Contract Signed':
            return 'Cerrado / OK'
        elif row['dias_inactivo'] > 10:
            return 'ALERTA: SLA Vencido'
        else:
            return 'En tiempo y forma'

    df['estado_sla'] = df.apply(clasificar_alerta, axis=1)

    print(" Guardando datos limpios...")
    # 7. Asegurar que la carpeta data_processed exista y exportar
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print("\n✅ Proceso completado con éxito. Resumen de Operaciones:")
    print(f"- Total de registros procesados: {len(df)}")
    print(f"- Registros duplicados detectados: {df['es_duplicado'].sum()}")
    print(f"- Casos con SLA vencido: {(df['estado_sla'] == 'ALERTA: SLA Vencido').sum()}")

if __name__ == "__main__":
    run_ops_pipeline()