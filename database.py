import os
import json
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pickle
import base64

# Obtener la URL de conexión a la base de datos desde variables de entorno
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Verificar que tenemos una URL válida para la base de datos
if not DATABASE_URL:
    print("Advertencia: No se encontró la URL de la base de datos. Usando SQLite en memoria.")
    DATABASE_URL = "sqlite:///:memory:"

# Crear el motor de base de datos
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Definir el modelo de datos para los informes
class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    filename = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    dataframe = Column(Text)  # DataFrame serializado
    metrics = Column(Text)  # Métricas serializadas como JSON
    analysis = Column(Text)  # Análisis serializado como JSON

# Crear las tablas
Base.metadata.create_all(engine)

# Crear una sesión para interactuar con la base de datos
Session = sessionmaker(bind=engine)

def serialize_dataframe(df):
    """
    Serializa un DataFrame de pandas a un string base64 para guardarlo en la base de datos.
    """
    return base64.b64encode(pickle.dumps(df)).decode('utf-8')

def deserialize_dataframe(serialized_df):
    """
    Deserializa un string base64 a un DataFrame de pandas.
    """
    return pickle.loads(base64.b64decode(serialized_df.encode('utf-8')))

def save_report_to_db(df, date, filename=None, metrics=None, analysis=None):
    """
    Guarda un informe en la base de datos.
    
    Args:
        df: DataFrame de pandas con los datos
        date: Fecha del informe (objeto datetime.date)
        filename: Nombre del archivo original (opcional)
        metrics: Diccionario de métricas (opcional)
        analysis: Diccionario de resultados de análisis (opcional)
        
    Returns:
        Boolean indicando éxito o fracaso
    """
    session = None
    try:
        session = Session()
        
        # Serializar el DataFrame
        serialized_df = serialize_dataframe(df)
        
        # Serializar métricas y análisis
        serialized_metrics = json.dumps(metrics) if metrics else None
        serialized_analysis = json.dumps(analysis) if analysis else None
        
        # Verificar si ya existe un informe para esta fecha
        existing_report = session.query(Report).filter(Report.date == date).first()
        
        if existing_report:
            # Actualizar el informe existente
            existing_report.filename = filename
            existing_report.dataframe = serialized_df
            existing_report.metrics = serialized_metrics
            existing_report.analysis = serialized_analysis
            existing_report.created_at = datetime.now()
        else:
            # Crear un nuevo registro de informe
            new_report = Report(
                date=date,
                filename=filename,
                dataframe=serialized_df,
                metrics=serialized_metrics,
                analysis=serialized_analysis
            )
            # Agregar el nuevo informe
            session.add(new_report)
        
        # Guardar los cambios
        session.commit()
        return True
    
    except Exception as e:
        print(f"Error al guardar el informe en la base de datos: {str(e)}")
        if session:
            session.rollback()
        return False
    
    finally:
        if session:
            session.close()

def load_report_from_db(date):
    """
    Carga un informe desde la base de datos.
    
    Args:
        date: Fecha del informe (objeto datetime.date)
        
    Returns:
        Diccionario con los datos del informe o None si falló
    """
    session = None
    try:
        session = Session()
        
        # Buscar el informe por fecha
        report = session.query(Report).filter(Report.date == date).first()
        
        if not report:
            return None
        
        # Deserializar el DataFrame
        df = deserialize_dataframe(report.dataframe)
        
        # Deserializar métricas y análisis
        metrics_str = str(report.metrics) if report.metrics else '{}'
        analysis_str = str(report.analysis) if report.analysis else '{}'
        
        try:
            metrics = json.loads(metrics_str)
        except:
            metrics = {}
            
        try:
            analysis = json.loads(analysis_str)
        except:
            analysis = {}
        
        # Preparar los metadatos
        metadata = {
            'date': report.date.strftime('%Y-%m-%d'),
            'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if report.filename:
            metadata['filename'] = report.filename
        
        # Devolver los datos en formato de diccionario
        return {
            'data': df,
            'metrics': metrics,
            'analysis': analysis,
            'metadata': metadata
        }
    
    except Exception as e:
        print(f"Error al cargar el informe desde la base de datos: {str(e)}")
        return None
    
    finally:
        if session:
            session.close()

def get_saved_report_dates_from_db():
    """
    Obtiene una lista de fechas para las que hay informes guardados.
    
    Returns:
        Lista de objetos datetime.date
    """
    session = None
    try:
        session = Session()
        
        # Consultar todas las fechas de informes
        reports = session.query(Report.date).order_by(Report.date.desc()).all()
        
        # Extraer las fechas
        dates = [report.date.date() for report in reports]
        
        return dates
    
    except Exception as e:
        print(f"Error al obtener las fechas de informes guardados: {str(e)}")
        return []
    
    finally:
        if session:
            session.close()

def delete_report_from_db(date):
    """
    Elimina un informe de la base de datos.
    
    Args:
        date: Fecha del informe (objeto datetime.date)
        
    Returns:
        Boolean indicando éxito o fracaso
    """
    session = None
    try:
        session = Session()
        
        # Buscar el informe por fecha
        report = session.query(Report).filter(Report.date == date).first()
        
        if not report:
            return False
        
        # Eliminar el informe
        session.delete(report)
        session.commit()
        
        return True
    
    except Exception as e:
        print(f"Error al eliminar el informe de la base de datos: {str(e)}")
        if session:
            session.rollback()
        return False
    
    finally:
        if session:
            session.close()