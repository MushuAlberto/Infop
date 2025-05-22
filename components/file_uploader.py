import streamlit as st
import pandas as pd
import os
import tempfile

def render_uploader():
    """
    Renders the file uploader component.
    
    Returns:
        The uploaded file object or None
    """
    uploaded_file = st.file_uploader(
        "Subir archivo Excel (.xlsx o .xlsm)",
        type=["xlsx", "xlsm"],
        help="El archivo debe contener una hoja llamada 'Base de Datos'"
    )
    
    return uploaded_file

def process_excel_file(uploaded_file):
    """
    Processes the uploaded Excel file and returns a pandas DataFrame.
    
    Args:
        uploaded_file: The uploaded file object from st.file_uploader
        
    Returns:
        pandas.DataFrame or None if validation fails
    """
    if uploaded_file is None:
        return None
    
    try:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # First check if the file has the required sheet
        xls = pd.ExcelFile(tmp_file_path)
        if 'Base de Datos' not in xls.sheet_names:
            st.error("El archivo Excel subido no contiene una hoja 'Base de Datos'.")
            os.unlink(tmp_file_path)  # Delete the temporary file
            return None
        
        # Read the sheet into a DataFrame, preserving data types
        df = pd.read_excel(
            tmp_file_path,
            sheet_name='Base de Datos',
            parse_dates=True,
            engine='openpyxl'
        )
        
        # Clean up the temporary file
        os.unlink(tmp_file_path)
        
        # Basic validation
        if df.empty:
            st.error("La hoja 'Base de Datos' está vacía.")
            return None
        
        # Check if there's at least one date column for filtering
        date_columns = df.select_dtypes(include=['datetime64']).columns
        if len(date_columns) == 0:
            st.warning("No se detectaron columnas de fecha. Algunas funciones pueden no trabajar correctamente.")
        
        # Save the raw file for reference
        save_path = os.path.join('data', 'raw', uploaded_file.name)
        with open(save_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        st.success(f"Archivo '{uploaded_file.name}' procesado exitosamente.")
        return df
    
    except Exception as e:
        st.error(f"Error al procesar el archivo Excel: {str(e)}")
        # Clean up the temporary file if it exists
        tmp_file_path = locals().get('tmp_file_path')
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        return None
