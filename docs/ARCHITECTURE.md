# Adapt Tools System Architecture

## Overview
Adapt Tools is a comprehensive data adaptation and visualization platform designed to simplify the process of importing, storing, and presenting structured data. It enables users to convert Excel spreadsheets into a structured, queryable format that can be accessed and explored through an intuitive web interface.

## Components
- **app/Streamlit**: The primary user-facing application built with Streamlit, providing interactive data visualization and exploration capabilities. It connects to the database to retrieve and display processed data.
- **web/Nginx**: The web server configured as a reverse proxy that routes incoming requests to the appropriate services. It also serves static assets and handles SSL termination if needed.
- **db/MySQL**: The relational database system responsible for storing all imported and processed data securely and efficiently, supporting complex queries required by the application.
- **phpMyAdmin**: A web-based administrative interface for managing the MySQL database, allowing for direct database inspection, query execution, and data management by administrators.

## Data Flow
The data flow begins with Excel files being imported through a dedicated importer script. This script processes the raw Excel data and loads it into the MySQL database in a structured format. The Streamlit application then queries this database to deliver dynamic and interactive data views to end users.

```
Excel → Importer Script → MySQL Database → Streamlit Application → End User
           ↑
    phpMyAdmin (Database Management)
```
