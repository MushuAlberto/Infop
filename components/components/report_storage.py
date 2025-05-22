import streamlit as st
import pandas as pd
import os
import json
import pickle
from datetime import datetime
import database as db

def save_report(df, date, metrics=None, analysis=None):
    """
    Saves the report data to the database.
    
    Args:
        df: The pandas DataFrame containing the filtered data
        date: The date of the report (datetime.date object)
        metrics: Dictionary of metrics (optional)
        analysis: Dictionary of analysis results (optional)
        
    Returns:
        Boolean indicating success or failure
    """
    try:
        # Preparar métricas serializables
        if metrics:
            serializable_metrics = {}
            for key, value in metrics.items():
                if isinstance(value, dict):
                    serializable_metrics[key] = {k: float(v) if isinstance(v, (int, float, complex)) else v for k, v in value.items()}
                else:
                    serializable_metrics[key] = float(value) if isinstance(value, (int, float, complex)) else value
        else:
            serializable_metrics = None
            
        # Guardar en la base de datos
        success = db.save_report_to_db(
            df=df,
            date=date,
            metrics=serializable_metrics,
            analysis=analysis
        )
        
        # También guardamos en el sistema de archivos como respaldo
        try:
            # Create directory structure
            report_dir = os.path.join('data', 'processed', date.strftime('%Y-%m-%d'))
            os.makedirs(report_dir, exist_ok=True)
            
            # Save data to CSV
            df.to_csv(os.path.join(report_dir, 'data.csv'), index=False)
            
            # Save a pickle file of the DataFrame for easier reloading
            with open(os.path.join(report_dir, 'data.pkl'), 'wb') as f:
                pickle.dump(df, f)
        except Exception as e:
            # Si falla el respaldo en archivos, solo lo registramos pero continuamos
            print(f"Advertencia: respaldo en sistema de archivos falló: {str(e)}")
            
        return success
    
    except Exception as e:
        st.error(f"Error al guardar el informe: {str(e)}")
        return False

def load_report(date):
    """
    Loads a saved report from the database.
    
    Args:
        date: The date of the report (datetime.date object)
        
    Returns:
        Dictionary containing the loaded report data or None if failed
    """
    try:
        # Intentar cargar desde la base de datos
        report_data = db.load_report_from_db(date)
        
        if report_data:
            return report_data
        
        # Si no está en la base de datos, intentar cargarlo del sistema de archivos (compatibilidad hacia atrás)
        report_dir = os.path.join('data', 'processed', date.strftime('%Y-%m-%d'))
        
        # Verificar si el directorio existe
        if not os.path.exists(report_dir):
            st.error(f"No se encontró ningún informe para {date.strftime('%Y-%m-%d')}.")
            return None
        
        # Cargar datos desde el archivo pickle
        data_path = os.path.join(report_dir, 'data.pkl')
        if os.path.exists(data_path):
            with open(data_path, 'rb') as f:
                df = pickle.load(f)
        else:
            # Si no existe el pickle, intentar con CSV
            csv_path = os.path.join(report_dir, 'data.csv')
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
            else:
                st.error("No se encontró el archivo de datos.")
                return None
        
        # Cargar metadata
        metadata_path = os.path.join(report_dir, 'metadata.json')
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    
                # Extraer métricas y análisis
                metrics = metadata.get('metrics', {})
                analysis = metadata.get('analysis', {})
                
                # Guardar en la base de datos para futuras consultas
                try:
                    db.save_report_to_db(df, date, None, metrics, analysis)
                except Exception as db_e:
                    print(f"No se pudo sincronizar con la base de datos: {str(db_e)}")
                
                return {
                    'data': df,
                    'metrics': metrics,
                    'analysis': analysis,
                    'metadata': metadata
                }
            except Exception as json_e:
                print(f"Error al cargar metadata: {str(json_e)}")
                # Continuar sin metadata
        else:
            # Devolver solo los datos si no se encuentra metadata
            return {
                'data': df,
                'metrics': {},
                'analysis': {}
            }
    
    except Exception as e:
        st.error(f"Error al cargar el informe: {str(e)}")
        return None

def get_saved_report_dates():
    """
    Gets a list of dates for which reports are saved.
    
    Returns:
        List of datetime.date objects
    """
    try:
        # Obtener fechas de la base de datos
        db_dates = db.get_saved_report_dates_from_db()
        
        # Si hay fechas en la base de datos, devolverlas
        if db_dates:
            return db_dates
            
        # Si no hay fechas en la base de datos, buscar en el sistema de archivos (compatibilidad hacia atrás)
        processed_dir = os.path.join('data', 'processed')
        
        # Verificar si el directorio existe
        if not os.path.exists(processed_dir):
            return []
        
        # Obtener lista de subdirectorios (fechas)
        dates = []
        for dir_name in os.listdir(processed_dir):
            try:
                # Intentar analizar el nombre del directorio como una fecha
                date = datetime.strptime(dir_name, '%Y-%m-%d').date()
                
                # Verificar si es un informe válido buscando archivos necesarios
                report_dir = os.path.join(processed_dir, dir_name)
                if os.path.exists(os.path.join(report_dir, 'data.csv')) or \
                   os.path.exists(os.path.join(report_dir, 'data.pkl')):
                    dates.append(date)
            except ValueError:
                # Omitir directorios que no coinciden con el formato de fecha
                continue
        
        # Ordenar fechas en orden descendente (más recientes primero)
        dates.sort(reverse=True)
        
        return dates
    
    except Exception as e:
        st.error(f"Error al obtener las fechas de informes guardados: {str(e)}")
        return []
