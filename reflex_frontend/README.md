# SunWindSCADA Frontend

A real-time SCADA dashboard for monitoring wind turbines, built with Reflex.

## Prerequisites

- Docker and Docker Compose
- Python 3.12+
- Node.js 16+ (for local development)

## Getting Started

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/SunWindSCADA.git
cd SunWindSCADA/reflex_frontend
```

2. **Set up environment variables**

Copy the example environment file and update the values as needed:

```bash
cp .env.example .env
```

3. **Run with Docker (Recommended)**

```bash
docker-compose up --build
```

4. **Run locally**

```bash
# Install dependencies
pip install -r requirements.txt

# Start the Reflex app
reflex run
```

The application will be available at `http://localhost:3000`.

## Project Structure

- `reflex_frontend/` - Main application package
  - `__init__.py` - Main application code and UI components
  - `rxconfig.py` - Reflex configuration
  - `.env` - Environment variables (not version controlled)
  - `requirements.txt` - Python dependencies
  - `Dockerfile.reflex` - Docker configuration for the Reflex app

## Development

### Running Tests

```bash
pytest
```

### Building for Production

```bash
reflex export --frontend-only
```

This will create a `frontend` directory with the compiled frontend assets that can be served by any static file server.

## Deployment

The application can be deployed using Docker Compose:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
