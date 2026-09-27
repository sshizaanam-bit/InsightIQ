# InsightIQ – AI Business Intelligence Platform

InsightIQ is a web-based Business Intelligence platform designed to make
data analysis easier for users by combining data processing, visualization,
dashboarding, and natural-language analysis in one application.

## Overview

InsightIQ allows users to upload structured datasets and explore their data
through automated analysis and interactive visualizations.

The platform is designed to help users identify patterns, trends, missing
values, duplicates, categorical distributions, and other useful insights
without requiring advanced programming knowledge.

## Key Features

- CSV, XLS, and XLSX dataset upload
- Dataset preview
- Automatic row and column analysis
- Missing-value detection
- Duplicate-value detection
- Numerical data summaries
- Categorical data analysis
- Interactive data visualizations
- Business Intelligence dashboard
- Natural-language data analysis
- Automated analytical reports
- Responsive web interface

## Technology Stack

### Backend
- Python
- Flask
- Pandas
- NumPy

### Data Visualization
- Plotly

### Frontend
- HTML
- CSS
- JavaScript
- Bootstrap

### Database
- SQLite

### Reporting
- ReportLab

## Project Structure

```text
InsightIQ/
│
├── static/
│   ├── charts/
│   ├── css/
│   ├── images/
│   └── js/
│
├── templates/
│   ├── dashboard.html
│   ├── index.html
│   ├── layout.html
│   ├── report.html
│   └── upload.html
│
├── uploads/
├── venv/
├── app.py
├── database.db
├── requirements.txt
└── README.md