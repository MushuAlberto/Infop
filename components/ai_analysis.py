import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_analysis(df, metrics):
    """
    Generates AI analysis of the data.
    
    Args:
        df: The pandas DataFrame containing the filtered data
        metrics: Dictionary of metrics
        
    Returns:
        Dictionary containing analysis results
    """
    analysis = {
        'summary': '',
        'trends': [],
        'anomalies': [],
        'insights': []
    }
    
    if df.empty:
        analysis['summary'] = "No data available for analysis."
        return analysis
    
    # Basic summary
    record_count = metrics.get('record_count', 0)
    analysis['summary'] = f"Analysis based on {record_count} records."
    
    # Get numeric columns for analysis
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    # Skip if no numeric data
    if not numeric_cols:
        analysis['summary'] += " No numeric data available for detailed analysis."
        return analysis
    
    # Identify trends in numeric columns
    for col in numeric_cols:
        # Skip if we don't have metrics for this column
        if col not in metrics:
            continue
        
        col_metrics = metrics[col]
        
        # Check if there's enough data for trend analysis
        if col_metrics['count'] < 3:
            continue
        
        # Check for basic trends (high variance might indicate trend)
        if col_metrics['std'] > 0.5 * col_metrics['mean'] and col_metrics['mean'] != 0:
            analysis['trends'].append(f"High variability detected in {col} (coefficient of variation: {col_metrics['std']/col_metrics['mean']:.2f}).")
    
    # Check for anomalies (outliers)
    for col in numeric_cols:
        # Skip if we don't have metrics for this column
        if col not in metrics:
            continue
        
        col_metrics = metrics[col]
        
        # Simple outlier detection: values beyond 3 standard deviations
        if col_metrics['std'] > 0:
            upper_bound = col_metrics['mean'] + 3 * col_metrics['std']
            lower_bound = col_metrics['mean'] - 3 * col_metrics['std']
            
            # Count outliers
            outliers = df[(df[col] > upper_bound) | (df[col] < lower_bound)]
            outlier_count = len(outliers)
            
            if outlier_count > 0:
                percentage = (outlier_count / col_metrics['count']) * 100
                analysis['anomalies'].append(f"Found {outlier_count} outliers ({percentage:.1f}%) in {col}.")
    
    # Generate insights based on the data
    # 1. Look for correlations between numeric columns
    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr()
        
        # Find strong correlations (>0.7 or <-0.7)
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                if abs(corr_matrix.iloc[i, j]) > 0.7:
                    col1 = numeric_cols[i]
                    col2 = numeric_cols[j]
                    corr = corr_matrix.iloc[i, j]
                    
                    if corr > 0:
                        analysis['insights'].append(f"Strong positive correlation ({corr:.2f}) found between {col1} and {col2}.")
                    else:
                        analysis['insights'].append(f"Strong negative correlation ({corr:.2f}) found between {col1} and {col2}.")
    
    # 2. Identify largest contributors
    # For each numeric column, find categories that contribute most to the total
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if categorical_cols:
        for cat_col in categorical_cols[:2]:  # Limit to first 2 categorical columns
            for num_col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                # Group by category and sum the numeric value
                grouped = df.groupby(cat_col)[num_col].sum().reset_index()
                
                # Sort and get top contributor
                if not grouped.empty:
                    grouped = grouped.sort_values(num_col, ascending=False)
                    top_category = grouped.iloc[0][cat_col]
                    contribution = grouped.iloc[0][num_col]
                    total = df[num_col].sum()
                    
                    if total > 0:
                        percentage = (contribution / total) * 100
                        analysis['insights'].append(f"{top_category} accounts for {percentage:.1f}% of total {num_col}.")
    
    # Time-based analysis if date columns exist
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    if date_cols and numeric_cols:
        date_col = date_cols[0]  # Use first date column
        
        # Check if we have at least 2 different dates
        unique_dates = df[date_col].dt.date.nunique()
        
        if unique_dates > 1:
            # Sort by date
            df_sorted = df.sort_values(date_col)
            
            # Get first and last date
            first_date = df_sorted[date_col].iloc[0]
            last_date = df_sorted[date_col].iloc[-1]
            
            # Check if there's a clear time trend
            for num_col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                first_value = df_sorted[num_col].iloc[0]
                last_value = df_sorted[num_col].iloc[-1]
                
                if first_value != 0:
                    change_pct = ((last_value - first_value) / first_value) * 100
                    
                    if abs(change_pct) > 10:  # Only report significant changes
                        if change_pct > 0:
                            analysis['trends'].append(f"{num_col} increased by {change_pct:.1f}% from {first_date.date()} to {last_date.date()}.")
                        else:
                            analysis['trends'].append(f"{num_col} decreased by {abs(change_pct):.1f}% from {first_date.date()} to {last_date.date()}.")
    
    # Generate summary statement
    if analysis['trends'] or analysis['anomalies'] or analysis['insights']:
        analysis['summary'] += " Key findings include:"
        
        if analysis['trends']:
            analysis['summary'] += f" {len(analysis['trends'])} trends,"
        
        if analysis['anomalies']:
            analysis['summary'] += f" {len(analysis['anomalies'])} anomalies,"
        
        if analysis['insights']:
            analysis['summary'] += f" and {len(analysis['insights'])} insights."
    else:
        analysis['summary'] += " No significant patterns or anomalies detected in the data."
    
    return analysis

def display_analysis(analysis):
    """
    Displays the AI analysis results.
    
    Args:
        analysis: Dictionary containing analysis results from generate_analysis()
    """
    # Display summary
    st.subheader("Resumen del Análisis de IA")
    st.write(analysis['summary'])
    
    # Display details in expandable sections
    if analysis['trends']:
        with st.expander("Tendencias Detectadas", expanded=True):
            for trend in analysis['trends']:
                st.info(trend)
    
    if analysis['anomalies']:
        with st.expander("Anomalías Detectadas", expanded=True):
            for anomaly in analysis['anomalies']:
                st.warning(anomaly)
    
    if analysis['insights']:
        with st.expander("Insights Clave", expanded=True):
            for insight in analysis['insights']:
                st.success(insight)
    
    # Display general recommendations
    st.subheader("Recomendaciones")
    
    recommendations = []
    
    if analysis['trends']:
        recommendations.append("Monitorear las tendencias identificadas para detectar cambios futuros.")
    
    if analysis['anomalies']:
        recommendations.append("Investigar las anomalías para determinar si representan errores o valores atípicos importantes.")
    
    if analysis['insights']:
        recommendations.append("Concentrarse en los contribuyentes clave identificados en la sección de insights.")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    else:
        st.write("No hay recomendaciones específicas basadas en los datos actuales.")
