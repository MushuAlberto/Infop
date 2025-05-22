# Operational Data Analysis Tool - Architecture Guide

## Overview

This is a Streamlit-based web application for analyzing operational data from Excel files. The application allows users to upload Excel files, filter data by date, generate reports with metrics, create interactive visualizations, perform AI-based analysis of the data, and save reports for future reference.

The tool is designed to process Excel files that contain a "Base de Datos" sheet, generate insights, and provide both visual and textual analysis of the operational data.

## User Preferences

```
Preferred communication style: Simple, everyday language.
```

## System Architecture

The application follows a modular component-based architecture, where functionality is separated into distinct Python modules under the `components` directory. The main application (`app.py`) serves as the entry point and orchestrates these components.

### Data Flow

1. **User Input**: Users upload Excel files and select date filters through the Streamlit UI
2. **Data Processing**: Files are validated, parsed, and loaded into pandas DataFrames
3. **Analysis**: The system generates metrics, visualizations, and AI-based insights
4. **Output**: Users can view reports, interactive dashboards, and export/save results

### Directory Structure

```
/
├── app.py                 # Main application entry point
├── components/            # Modular functionality components
│   ├── ai_analysis.py     # AI-based data analysis 
│   ├── dashboard.py       # Interactive visualization dashboard
│   ├── data_filter.py     # Date filtering functionality
│   ├── file_uploader.py   # Excel file upload and processing
│   ├── report_generator.py # Metrics calculation and report generation
│   └── report_storage.py  # Saving reports to the filesystem
├── data/                  # Data storage directory
│   ├── raw/               # Raw uploaded files
│   └── processed/         # Processed reports and analysis
└── .streamlit/            # Streamlit configuration
    └── config.toml        # Streamlit server and theme settings
```

## Key Components

### 1. File Uploader (`components/file_uploader.py`)

Handles the uploading and validation of Excel files. It ensures that:
- Only .xlsx or .xlsm files are accepted
- The file contains a "Base de Datos" sheet
- Data types are preserved during import

### 2. Data Filter (`components/data_filter.py`)

Provides date-based filtering functionality:
- Automatically detects date columns in the uploaded data
- Allows users to select a date column for filtering
- Supports filtering by a single date or date range
- Updates the session state with filtered data

### 3. Report Generator (`components/report_generator.py`)

Generates analytical reports from the filtered data:
- Calculates key metrics (mean, median, min, max, sum, standard deviation)
- Creates visual representations of the data
- Supports export to Excel and PDF formats

### 4. Dashboard (`components/dashboard.py`)

Creates interactive visualizations:
- Provides UI filters for categorical data
- Generates dynamic, interactive charts using Plotly
- Updates in real-time based on user selections

### 5. AI Analysis (`components/ai_analysis.py`)

Performs automated analysis of the data:
- Identifies trends in the data
- Detects anomalies and outliers
- Generates insights in natural language
- Summarizes key findings for quick understanding

### 6. Report Storage (`components/report_storage.py`)

Manages the persistence of reports:
- Saves filtered data to CSV files
- Stores metrics and analysis results in JSON format
- Organizes reports by date in the file system
- Creates a structured directory hierarchy for easy retrieval

## External Dependencies

The application relies on several key Python libraries:

1. **Streamlit**: The core framework for building the web interface
2. **Pandas**: For data manipulation and analysis
3. **Plotly/Matplotlib/Seaborn**: For data visualization
4. **Excel Libraries**: openpyxl, xlrd, and xlsxwriter for Excel file operations
5. **PDF Generation**: weasyprint for PDF report creation

## Deployment Strategy

The application is configured to run as a Streamlit web service:

1. **Server Configuration**: 
   - Headless mode enabled
   - Listens on 0.0.0.0:5000 to accept external connections
   - Custom theme with professional color scheme

2. **Execution**:
   - Entry point is `app.py`
   - Running via `streamlit run app.py --server.port 5000`
   - Set up for autoscaling deployment

3. **Environment**:
   - Python 3.11 runtime
   - Nix-managed dependencies for system libraries
   - Workflows configured for easy launching

## Development Guidelines

When extending this application:

1. Keep the modular structure by adding new functionality as components
2. Maintain the state management approach using Streamlit's session_state
3. Follow the existing patterns for data processing and visualization
4. Ensure proper error handling for file operations and data processing
5. Add new visualization types to the dashboard component as needed
6. Extend the AI analysis with more sophisticated techniques when required