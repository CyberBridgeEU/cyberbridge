# config/environment.py
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_api_base_url():
    """
    Automatically detect environment and return appropriate API base URL.
    Detection logic mirrors the database configuration approach.
    """
    container_env = os.getenv("CONTAINER_ENV")
    db_host = os.getenv("DB_HOST")

    # Check if we're running in a container (production environment)
    if container_env == "docker" or db_host:
        # Production: Running in Docker container
        # API_BASE_URL_PROD should be set via Docker build arg
        api_url = os.getenv("API_BASE_URL_PROD")
        if not api_url:
            logger.warning("API_BASE_URL_PROD not set! Using fallback.")
            api_url = "http://localhost:5174"
        logger.info(f"Production environment detected. Using API base URL: {api_url}")
        return api_url
    else:
        # Development: Running locally
        api_url = os.getenv("API_BASE_URL_DEV", "http://localhost:8000")
        logger.info(f"Development environment detected. Using API base URL: {api_url}")
        return api_url

def is_production_environment():
    """
    Check if we're running in production environment.
    """
    container_env = os.getenv("CONTAINER_ENV")
    db_host = os.getenv("DB_HOST")
    return container_env == "docker" or db_host is not None

def get_frontend_url():
    """
    Automatically detect environment and return appropriate frontend URL.
    """
    if is_production_environment():
        frontend_url = os.getenv("FRONTEND_URL_PROD", "https://access.cyberbridge.eu")
        logger.info(f"Production environment detected. Using frontend URL: {frontend_url}")
        return frontend_url
    else:
        frontend_url = os.getenv("FRONTEND_URL_DEV", "http://localhost:5173")
        logger.info(f"Development environment detected. Using frontend URL: {frontend_url}")
        return frontend_url

def get_environment_name():
    """
    Get human-readable environment name.
    """
    return "production" if is_production_environment() else "development"