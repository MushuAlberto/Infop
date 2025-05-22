import streamlit as st
import pandas as pd
import datetime
from datetime import date
from typing import Union, Tuple

def render_date_filter(df):
    """
    Renders the date filter component and updates the session state with filtered data.
    
    Args:
        df: The pandas DataFrame to filter
        
    Returns:
        The selected date or date range
    """
    # Find date columns
    date_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    # If no date columns found, try to find columns that might be dates but were parsed as strings
    if not date_columns:
        for col in df.columns:
            if 'date' in col.lower() or 'fecha' in col.lower():
                try:
                    # Try to convert to datetime
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    if not df[col].isna().all():  # If not all values are NaN
                        date_columns.append(col)
                except:
                    pass
    
    if not date_columns:
        st.warning("No se encontraron columnas de fecha en los datos. No es posible filtrar por fecha.")
        return None
    
    # Let user select which date column to use for filtering
    date_column = st.selectbox(
        "Selecciona columna de fecha para filtrar",
        options=date_columns,
        index=0
    )
    
    # Get min and max dates from the selected column
    try:
        min_date = df[date_column].min().date()
        max_date = df[date_column].max().date()
    except:
        st.error(f"Error al obtener el rango de fechas de la columna {date_column}")
        return None
    
    # Date selection: single date or range
    filter_type = st.radio(
        "Tipo de filtro",
        options=["Fecha Única", "Rango de Fechas"],
        horizontal=True
    )
    
    if filter_type == "Fecha Única":
        selected_date = st.date_input(
            "Selecciona fecha",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
        
        # Convert to datetime for filtering
        filter_date = pd.to_datetime(selected_date)
        
        # Filter the dataframe
        filtered_df = df[df[date_column].dt.date == selected_date]
        
        # Store in session state
        st.session_state.filtered_df = filtered_df
        st.session_state.selected_date = selected_date
        
        return selected_date
    
    else:  # Date Range
        # Para evitar errores con el tipo de retorno del date_input
        try:
            # Intentar configurar un rango predeterminado de 7 días
            default_start = max_date - datetime.timedelta(days=7)
            date_range = st.date_input(
                "Selecciona rango de fechas",
                value=[default_start, max_date],
                min_value=min_date,
                max_value=max_date
            )
            
            # Manejar el resultado - más seguro usar el método list()
            date_list = list(date_range) if hasattr(date_range, '__iter__') else [date_range]
            
            # Obtener fecha inicial y final
            start_date = date_list[0] if date_list else max_date
            end_date = date_list[-1] if len(date_list) > 1 else start_date
        except Exception as e:
            st.error(f"Error al seleccionar el rango de fechas: {str(e)}")
            # En caso de error, usar la fecha más reciente
            start_date = end_date = max_date
        
        # Handle single date selection when using date_input with a range
        if start_date == end_date:
            filtered_df = df[df[date_column].dt.date == start_date]
        else:
            # Filter the dataframe for the date range
            filtered_df = df[(df[date_column].dt.date >= start_date) & 
                            (df[date_column].dt.date <= end_date)]
        
        # Store in session state
        st.session_state.filtered_df = filtered_df
        st.session_state.selected_date = start_date if start_date == end_date else start_date  # Use start date as reference
        
        return (start_date, end_date)

def apply_filters(df, filters):
    """
    Applies additional filters to the DataFrame.
    
    Args:
        df: The pandas DataFrame to filter
        filters: Dictionary of {column: value} pairs to filter on
        
    Returns:
        Filtered pandas DataFrame
    """
    filtered_df = df.copy()
    
    for column, value in filters.items():
        if column in filtered_df.columns:
            if isinstance(value, list):
                filtered_df = filtered_df[filtered_df[column].isin(value)]
            else:
                filtered_df = filtered_df[filtered_df[column] == value]
    
    return filtered_df
