import streamlit as st
import os
import datetime
from components import file_uploader, report_generator, dashboard, ai_analysis, data_filter, report_storage
import database as db

# Create necessary directories if they don't exist
for dir_path in ["data/raw", "data/processed"]:
    os.makedirs(dir_path, exist_ok=True)

# Set page config
st.set_page_config(
    page_title="Herramienta de Análisis de Datos Operacionales",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("Herramienta de Análisis de Datos Operacionales")
st.markdown("""
Esta aplicación te permite analizar datos operacionales desde archivos Excel.
Sube tu archivo Excel, selecciona una fecha, y obtén insights de tus datos.
""")

# Sidebar for file upload and date selection
with st.sidebar:
    st.header("Configuración")
    
    # File upload section
    uploaded_file = file_uploader.render_uploader()
    
    if uploaded_file:
        # Get the dataframe
        df = file_uploader.process_excel_file(uploaded_file)
        if df is not None:
            # Store the dataframe in session state
            st.session_state.df = df
            
            # Date range for filter
            date_range = data_filter.render_date_filter(df)
            
            # Save report button
            if st.button("Guardar Informe Actual"):
                if 'filtered_df' in st.session_state and 'selected_date' in st.session_state:
                    success = report_storage.save_report(
                        st.session_state.filtered_df,
                        st.session_state.selected_date,
                        st.session_state.metrics if 'metrics' in st.session_state else None,
                        st.session_state.analysis if 'analysis' in st.session_state else None
                    )
                    if success:
                        st.success("¡Informe guardado exitosamente!")
                    else:
                        st.error("Error al guardar el informe.")
                else:
                    st.warning("No hay datos para guardar. Por favor selecciona una fecha primero.")
    
    # Load saved reports section
    st.header("Cargar Informes Guardados")
    saved_dates = report_storage.get_saved_report_dates()
    
    if saved_dates:
        selected_saved_date = st.selectbox(
            "Selecciona un informe guardado",
            options=saved_dates,
            format_func=lambda x: x.strftime("%Y-%m-%d")
        )
        
        if st.button("Cargar Informe"):
            loaded_data = report_storage.load_report(selected_saved_date)
            if loaded_data:
                st.session_state.filtered_df = loaded_data["data"]
                st.session_state.metrics = loaded_data["metrics"]
                st.session_state.analysis = loaded_data["analysis"]
                st.session_state.selected_date = selected_saved_date
                st.success(f"Informe del {selected_saved_date.strftime('%Y-%m-%d')} cargado!")
                st.rerun()
            else:
                st.error("Error al cargar el informe.")
    else:
        st.info("No se encontraron informes guardados.")

# Main content area
if 'filtered_df' in st.session_state:
    # Display the date filter info
    if 'selected_date' in st.session_state:
        st.subheader(f"Datos para: {st.session_state.selected_date.strftime('%Y-%m-%d')}")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Informe", "Dashboard", "Análisis IA", "Base de Datos", "Descargar Proyecto"])
    
    with tab1:
        # Report view
        if 'filtered_df' in st.session_state:
            st.subheader("Informe Operacional")
            metrics = report_generator.generate_metrics(st.session_state.filtered_df)
            st.session_state.metrics = metrics
            report_generator.display_report(st.session_state.filtered_df, metrics)
    
    with tab2:
        # Dashboard view
        if 'filtered_df' in st.session_state:
            st.subheader("Dashboard Interactivo")
            dashboard.render_dashboard(st.session_state.filtered_df)
    
    with tab3:
        # AI Analysis view
        if 'filtered_df' in st.session_state and 'metrics' in st.session_state:
            st.subheader("Análisis de Inteligencia Artificial")
            analysis = ai_analysis.generate_analysis(
                st.session_state.filtered_df, 
                st.session_state.metrics
            )
            st.session_state.analysis = analysis
            ai_analysis.display_analysis(analysis)
    
    with tab4:
        # Database info view
        st.subheader("Información de la Base de Datos")
        st.write("Esta aplicación utiliza PostgreSQL para almacenar los informes y análisis generados.")
        
        # Obtener las fechas de informes guardados
        saved_dates = db.get_saved_report_dates_from_db()
        
        if saved_dates:
            st.success(f"Hay {len(saved_dates)} informes guardados en la base de datos.")
            
            # Mostrar informes en una tabla
            date_strings = [date.strftime('%Y-%m-%d') for date in saved_dates]
            
            import pandas as pd
            df_reports = pd.DataFrame({
                "Fecha": date_strings,
                "Acción": ["Ver" for _ in range(len(date_strings))]
            })
            
            st.dataframe(df_reports)
            
            # Opción para eliminar informes
            col1, col2 = st.columns(2)
            
            with col1:
                selected_date_to_delete = st.selectbox(
                    "Seleccionar informe para eliminar",
                    options=saved_dates,
                    format_func=lambda x: x.strftime("%Y-%m-%d")
                )
            
            with col2:
                if st.button("Eliminar Informe Seleccionado"):
                    if db.delete_report_from_db(selected_date_to_delete):
                        st.success(f"Informe del {selected_date_to_delete.strftime('%Y-%m-%d')} eliminado exitosamente.")
                        st.rerun()
                    else:
                        st.error("Error al eliminar el informe.")
        else:
            st.info("No hay informes guardados en la base de datos.")
            
        # Mostrar información de conexión
        with st.expander("Detalles de Conexión"):
            st.code(f"""
            Host: {os.environ.get('PGHOST', 'No disponible')}
            Puerto: {os.environ.get('PGPORT', 'No disponible')}
            Base de Datos: {os.environ.get('PGDATABASE', 'No disponible')}
            """)
            
            # Ejecutar una consulta simple para verificar la conexión
            try:
                from sqlalchemy import text
                with db.engine.connect() as connection:
                    result = connection.execute(text("SELECT 1"))
                    row = result.fetchone()
                    if row and row[0] == 1:
                        st.success("Conexión a la base de datos establecida correctamente.")
                        st.info("La base de datos PostgreSQL proporciona almacenamiento persistente para todos los informes generados.")
                    else:
                        st.warning("La conexión a la base de datos parece incompleta.")
            except Exception as e:
                st.error(f"Error al conectar a la base de datos: {str(e)}")
                st.info("Mientras tanto, los informes se guardarán localmente como respaldo.")
    
    with tab5:
        # Pestaña para descargar el proyecto
        st.subheader("Descargar Código Fuente del Proyecto")
        st.markdown("""
        Aquí puedes descargar el código fuente completo de la aplicación de análisis de datos operacionales.
        Esto incluye todos los componentes, como:
        
        - Módulo de carga de archivos Excel
        - Sistema de filtrado por fecha
        - Generador de informes y métricas
        - Dashboard interactivo
        - Análisis de IA
        - Integración con base de datos PostgreSQL
        """)
        
        # Cargar el archivo ZIP y crear un botón de descarga
        import base64
        
        try:
            with open("proyecto_analisis_datos_2.zip", "rb") as f:
                zip_data = f.read()
                b64 = base64.b64encode(zip_data).decode()
                
            href = f'<a href="data:application/zip;base64,{b64}" download="proyecto_analisis_datos.zip">⬇️ Descargar Proyecto Completo (.zip)</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            st.success("El archivo contiene todo el código fuente y estructura necesaria para ejecutar la aplicación.")
            
        except Exception as e:
            st.error(f"No se pudo preparar el archivo de descarga: {str(e)}")
            st.info("Por favor contacta al administrador del sistema para obtener el código fuente.")

elif 'df' in st.session_state:
    # If we have data but no filters applied yet
    st.info("Por favor selecciona una fecha en la barra lateral para generar un informe.")
else:
    # Initial state
    st.info("Por favor sube un archivo Excel con una hoja 'Base de Datos' para comenzar.")
    
    # Display some sample images
    col1, col2 = st.columns(2)
    with col1:
        st.image("https://pixabay.com/get/g021729465f0443867e55aa94d556186d68c6a7d0aee052dff327b9d04ae17047a117a3bf2d26def21f882905cacf9dfa2f7333121337b3a31c23a5d6aa244497_1280.jpg", 
                 caption="Dashboard de Análisis de Datos", use_container_width=True)
    with col2:
        st.image("https://pixabay.com/get/g345c8cb93d1f1c33bd577ab66f11aeeca360f282a979f2e143bd2120402653d4c62cd4ddf08eb21fdd68cdf5a2a8c0436a84bcbaf7f0ca84591307618e33c144_1280.jpg", 
                 caption="Insights Operacionales", use_container_width=True)
