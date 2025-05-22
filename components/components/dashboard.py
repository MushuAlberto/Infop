import streamlit as st
import pandas as pd
import plotly.express as px
from plotly import graph_objects
from plotly.subplots import make_subplots

def render_dashboard(df):
    """
    Renders an interactive dashboard with visualizations.
    
    Args:
        df: The pandas DataFrame containing the filtered data
    """
    if df.empty:
        st.warning("No hay datos disponibles para visualizar en el dashboard.")
        return
    
    # Create filters
    st.sidebar.header("Filtros del Dashboard")
    
    # Get categorical columns for filtering
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Add filters for up to 3 categorical columns
    filter_values = {}
    for i, col in enumerate(categorical_cols[:3]):
        if len(df[col].unique()) < 50:  # Only add filter if not too many unique values
            unique_values = sorted(df[col].unique().tolist())
            selected_values = st.sidebar.multiselect(
                f"Filtrar por {col}",
                options=unique_values,
                default=unique_values
            )
            
            if selected_values:
                filter_values[col] = selected_values
    
    # Apply filters if any
    filtered_df = df.copy()
    for col, values in filter_values.items():
        filtered_df = filtered_df[filtered_df[col].isin(values)]
    
    # Main dashboard area
    st.subheader("Dashboard Visualizations")
    
    # Check if we still have data after filtering
    if filtered_df.empty:
        st.warning("No data available with the current filter settings.")
        return
    
    # Dashboard layout with tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["Overview", "Trends", "Comparisons"])
    
    with tab1:
        render_overview_charts(filtered_df)
    
    with tab2:
        render_trend_charts(filtered_df)
    
    with tab3:
        render_comparison_charts(filtered_df)

def render_overview_charts(df):
    """
    Renders overview charts for the dashboard.
    
    Args:
        df: The pandas DataFrame containing the filtered data
    """
    st.subheader("Data Overview")
    
    # Get numeric and date columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    if not numeric_cols:
        st.info("No hay columnas numéricas disponibles para visualización.")
        return
    
    # Select columns for visualization
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribution chart for a numeric column
        if numeric_cols:
            selected_numeric = st.selectbox(
                "Select column for distribution chart",
                options=numeric_cols
            )
            
            fig = px.histogram(
                df, 
                x=selected_numeric,
                title=f"Distribution of {selected_numeric}",
                color_discrete_sequence=['#0078D7']
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Pie chart for a categorical column
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        if categorical_cols:
            selected_cat = st.selectbox(
                "Select categorical column for pie chart",
                options=categorical_cols
            )
            
            # Count values and get top 10 categories if there are many
            value_counts = df[selected_cat].value_counts().reset_index()
            value_counts.columns = [selected_cat, 'count']
            
            if len(value_counts) > 10:
                # Keep top 10 and group others
                top_10 = value_counts.iloc[:10]
                others = pd.DataFrame({
                    selected_cat: ['Others'],
                    'count': [value_counts.iloc[10:]['count'].sum()]
                })
                value_counts = pd.concat([top_10, others])
            
            fig = px.pie(
                value_counts, 
                values='count', 
                names=selected_cat,
                title=f"Distribution by {selected_cat}"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics table
    st.subheader("Summary Statistics")
    
    if numeric_cols:
        summary_stats = df[numeric_cols].describe().transpose()
        st.dataframe(summary_stats.style.format("{:.2f}"))

def render_trend_charts(df):
    """
    Renders trend charts for the dashboard.
    
    Args:
        df: The pandas DataFrame containing the filtered data
    """
    st.subheader("Trend Analysis")
    
    # Check if we have date columns for trend analysis
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    if not date_cols:
        st.info("No date columns available for trend analysis.")
        return
    
    # Select date and metric columns
    selected_date = st.selectbox(
        "Select date column",
        options=date_cols
    )
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not numeric_cols:
        st.info("No numeric columns available for trend analysis.")
        return
    
    selected_metrics = st.multiselect(
        "Select metrics to visualize (up to 3)",
        options=numeric_cols,
        default=numeric_cols[:min(2, len(numeric_cols))]
    )
    
    # Limit to 3 metrics for clarity
    selected_metrics = selected_metrics[:3]
    
    if not selected_metrics:
        st.info("Please select at least one metric.")
        return
    
    # Aggregation level
    agg_level = st.selectbox(
        "Nivel de agregación",
        options=["Día", "Semana", "Mes"]
    )
    
    # Prepare data for trend chart
    df_copy = df.copy()
    
    # Create date groups based on selected aggregation
    if agg_level == "Día":
        df_copy['date_group'] = df_copy[selected_date].dt.date
    elif agg_level == "Semana":
        df_copy['date_group'] = df_copy[selected_date].dt.to_period('W').dt.start_time.dt.date
    else:  # Mes
        df_copy['date_group'] = df_copy[selected_date].dt.to_period('M').dt.start_time.dt.date
    
    # Aggregate data
    agg_dict = {metric: 'mean' for metric in selected_metrics}
    df_agg = df_copy.groupby('date_group').agg(agg_dict).reset_index()
    
    # Create trend chart
    import plotly.graph_objects as go  # Importación local para evitar errores
    fig = go.Figure()
    
    for metric in selected_metrics:
        fig.add_trace(
            go.Scatter(
                x=df_agg['date_group'],
                y=df_agg[metric],
                mode='lines+markers',
                name=metric
            )
        )
    
    fig.update_layout(
        title=f"Análisis de Tendencia por {agg_level}",
        xaxis_title="Fecha",
        yaxis_title="Valor",
        legend_title="Métricas",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_comparison_charts(df):
    """
    Renders comparison charts for the dashboard.
    
    Args:
        df: The pandas DataFrame containing the filtered data
    """
    st.subheader("Comparative Analysis")
    
    # Get categorical and numeric columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not categorical_cols or not numeric_cols:
        st.info("Need both categorical and numeric columns for comparison charts.")
        return
    
    # Select columns for comparison
    col1, col2 = st.columns(2)
    
    with col1:
        selected_cat = st.selectbox(
            "Select category for comparison",
            options=categorical_cols
        )
    
    with col2:
        selected_metric = st.selectbox(
            "Select metric to compare",
            options=numeric_cols
        )
    
    # Create comparison chart (bar chart)
    # Aggregate data
    comparison_data = df.groupby(selected_cat)[selected_metric].agg(['mean', 'sum']).reset_index()
    
    # Sort by mean value
    comparison_data = comparison_data.sort_values('mean', ascending=False)
    
    # Limit to top 10 categories if there are too many
    if len(comparison_data) > 10:
        comparison_data = comparison_data.head(10)
    
    # Choose which measure to display
    measure = st.radio(
        "Select measure",
        options=["mean", "sum"],
        horizontal=True
    )
    
    # Create bar chart
    fig = px.bar(
        comparison_data,
        x=selected_cat,
        y=measure,
        title=f"{measure.capitalize()} of {selected_metric} by {selected_cat}",
        color=measure,
        color_continuous_scale='Blues'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add a box plot for distribution comparison
    st.subheader(f"Distribution of {selected_metric} by {selected_cat}")
    
    # Limit to top 5 categories for box plot clarity
    top_categories = comparison_data[selected_cat].head(5).tolist()
    filtered_for_box = df[df[selected_cat].isin(top_categories)]
    
    fig = px.box(
        filtered_for_box,
        x=selected_cat,
        y=selected_metric,
        title=f"Distribution of {selected_metric} by {selected_cat} (Top 5)",
        color=selected_cat
    )
    
    st.plotly_chart(fig, use_container_width=True)
