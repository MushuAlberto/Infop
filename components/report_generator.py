import streamlit as st
import pandas as pd
import numpy as np
import io
import base64
import tempfile
import os
import xlsxwriter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def generate_metrics(df):
    """
    Generates key metrics from the DataFrame.
    
    Args:
        df: The pandas DataFrame containing the filtered data
        
    Returns:
        Dictionary of metrics
    """
    metrics = {}
    
    # Skip if dataframe is empty
    if df.empty:
        return metrics
    
    # Identify numeric columns for analysis
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    for col in numeric_cols:
        metrics[col] = {
            'mean': df[col].mean(),
            'median': df[col].median(),
            'min': df[col].min(),
            'max': df[col].max(),
            'sum': df[col].sum(),
            'std': df[col].std(),
            'count': df[col].count()
        }
    
    # Add record count
    metrics['record_count'] = len(df)
    
    return metrics

def display_report(df, metrics):
    """
    Displays the report with metrics and data.
    """
    if df.empty:
        st.warning("No hay datos disponibles para los filtros seleccionados.")
        return
    
    # Columnas a excluir
    columnas_excluir = ['M', 'N', 'O', 'P', 'Q', 'R', 'Y', 'Z', 'AA', 'AB', 'AO', 'AP']
    
    # Columnas de porcentaje
    columnas_porcentaje = ['AL', 'AT', 'AU']
    
    # Filtrar las columnas del DataFrame y las métricas
    df_display = df.drop(columns=columnas_excluir, errors='ignore')
    metrics = {k: v for k, v in metrics.items() if k not in columnas_excluir}
    
    # Convertir columnas de porcentaje a formato decimal y luego a porcentaje
    for col in columnas_porcentaje:
        if col in df_display.columns:
            df_display[col] = df_display[col].astype(float) / 100
            df_display[col] = df_display[col].map('{:.2%}'.format)
    
    # Display key metrics in a two-column layout
    st.subheader("Métricas Clave")
    
    if not metrics or len(metrics) <= 1:  # Only record_count
        st.info("No hay datos numéricos disponibles para el cálculo de métricas.")
    else:
        # Definir pares de métricas relacionadas (solo las que queremos mostrar)
        pares_metricas = {
            'MSD Bateas': ('E', 'F'),
            'M&Q Aljibes': ('G', 'H'),
            'Coseducam Bateas': ('I', 'J'),
            'Coseducam Aljibes': ('K', 'L'),
            'Nazar Bateas': ('S', 'T'),
            'Nazar Aljibes': ('U', 'V'),
            'Jorquera Aljibes': ('W', 'X'),
            'Ramplas MSD': ('AC', 'AD')
        }
        
        # Mostrar cada par de métricas
        for nombre, (col_prog, col_real) in pares_metricas.items():
            if col_prog in metrics and col_real in metrics:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        label=f"{nombre} Prog.",
                        value=f"{metrics[col_prog]['mean']:.2f}",
                        delta=f"Max: {metrics[col_prog]['max']:.2f}"
                    )
                
                with col2:
                    st.metric(
                        label=f"{nombre} Real",
                        value=f"{metrics[col_real]['mean']:.2f}",
                        delta=f"Max: {metrics[col_real]['max']:.2f}"
                    )
    
    # Display record count
    st.info(f"Total de registros: {metrics.get('record_count', 0)}")
    
    # Display the data table
    st.subheader("Informe Operacional")
    
    # Permitir selección de empresa
    empresas = sorted(df_display['empresa'].unique()) if 'empresa' in df_display.columns else []
    empresa_seleccionada = st.selectbox(
        "Seleccionar Empresa",
        options=empresas,
        index=0 if empresas else None
    )
    
    if empresa_seleccionada:
        # Filtrar datos por empresa
        df_empresa = df_display[df_display['empresa'] == empresa_seleccionada]
        
        # Crear dos columnas para Prog. y Real
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Programado")
            cols_prog = [col for col in df_empresa.columns if 'prog' in col.lower()]
            if cols_prog:
                st.dataframe(df_empresa[cols_prog])
            else:
                st.info("No hay datos programados disponibles")
        
        with col2:
            st.subheader("Real")
            cols_real = [col for col in df_empresa.columns if 'real' in col.lower()]
            if cols_real:
                st.dataframe(df_empresa[cols_real])
            else:
                st.info("No hay datos reales disponibles")
    
    # Export options
    st.subheader("Opciones de Exportación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Exportar a Excel"):
            excel_data = export_to_excel(df, metrics)
            st.download_button(
                label="Descargar archivo Excel",
                data=excel_data,
                file_name="informe.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("Exportar a PDF"):
            pdf_data = export_to_pdf(df, metrics)
            st.download_button(
                label="Descargar archivo PDF",
                data=pdf_data,
                file_name="informe.pdf",
                mime="application/pdf"
            )

def export_to_excel(df, metrics):
    """
    Exports the report data to Excel format.
    
    Args:
        df: The pandas DataFrame to export
        metrics: Dictionary of metrics
        
    Returns:
        Excel file as bytes
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write data to a sheet
        df.to_excel(writer, sheet_name='Data', index=False)
        
        # Create a sheet for metrics
        metrics_df = pd.DataFrame()
        
        for metric_name, metric_values in metrics.items():
            if metric_name != 'record_count':
                # Convert metric dictionary to a row in the dataframe
                metric_df = pd.DataFrame([metric_values], index=[metric_name])
                metrics_df = pd.concat([metrics_df, metric_df])
        
        if not metrics_df.empty:
            metrics_df.to_excel(writer, sheet_name='Metrics')
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        
        # Add a format for headers
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Apply formatting to the data sheet
        worksheet = writer.sheets['Data']
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 18)
    
    output.seek(0)
    return output.getvalue()

def export_to_pdf(df, metrics):
    """
    Exports the report data to PDF format.
    
    Args:
        df: The pandas DataFrame to export
        metrics: Dictionary of metrics
        
    Returns:
        PDF file as bytes
    """
    output = io.BytesIO()
    
    with PdfPages(output) as pdf:
        # First page: Metrics
        plt.figure(figsize=(10, 8))
        plt.title("Report Metrics", fontsize=16)
        plt.axis('off')
        
        metrics_text = "Key Metrics:\n\n"
        
        for metric_name, metric_values in metrics.items():
            if metric_name == 'record_count':
                metrics_text += f"Total Records: {metric_values}\n"
            else:
                metrics_text += f"{metric_name}:\n"
                for k, v in metric_values.items():
                    metrics_text += f"  - {k}: {v:.2f}\n"
                metrics_text += "\n"
        
        plt.text(0.1, 0.5, metrics_text, fontsize=12, verticalalignment='center')
        pdf.savefig()
        plt.close()
        
        # Second page: Data table
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.axis('tight')
        ax.axis('off')
        
        # Only include the first 20 rows to keep PDF manageable
        display_df = df.head(20)
        
        table = ax.table(
            cellText=display_df.values,
            colLabels=display_df.columns,
            loc='center',
            cellLoc='center'
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.5)
        
        plt.title(f"Data Table (First {len(display_df)} rows)", fontsize=16)
        pdf.savefig()
        plt.close()
    
    output.seek(0)
    return output.getvalue()