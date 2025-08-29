# Adapt Tools

A web application designed to manage and explore climate adaptation tools efficiently.

## Context

This project was developed as part of the FutureMed COST Action during a short-term scientific mission at CERFACS. It provides a centralized platform for climate adaptation tools, enhancing access and collaboration among researchers and practitioners.

## Features

- Dynamic filters for quickly locating relevant adaptation tools.
- Detailed pages for each tool with comprehensive information.
- Suggestion form to contribute new tools or updates.
- Image upload and management for tool illustrations.
- MySQL backend ensuring robust data storage and retrieval.

## Repository Structure

- `app/`: Source code of the application.
- `public/`: Public assets and frontend resources.
- `data/`: Sample data and import files.
- `sql/`: SQL scripts for database setup and migrations.
- `docs/`: Documentation including roadmap and additional resources.
- `docker-compose.yml`: Docker Compose configuration for containerized deployment.

## Quickstart

1. Build and start the application using Docker Compose:

   ```bash
   docker-compose build
   docker-compose up
   ```

2. Import initial data from the provided Excel files located in the `data/` directory.

## Environment Variables

Configure environment variables as needed by creating or updating the `.env` file in the project root. Refer to `.env.example` for the required keys and example values.

## Deployment

For production deployment, use a VPS or cloud server and secure the application with HTTPS. Adjust the Docker Compose configuration as necessary to enable scalable, secure hosting and consider using a reverse proxy for SSL termination.

## Roadmap

For upcoming features and planned improvements, see [docs/ROADMAP.md](docs/ROADMAP.md).

## License

This project is licensed under Apache-2.0.
