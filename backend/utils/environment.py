import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def is_railway_environment() -> bool:
    """Check if running in Railway environment"""
    return os.getenv("RAILWAY_ENVIRONMENT") is not None

def is_readonly_environment() -> bool:
    """Check if running in a read-only environment (like Railway)"""
    return is_railway_environment()

def get_environment_info() -> dict:
    """Get comprehensive environment information"""
    return {
        "is_railway": is_railway_environment(),
        "is_readonly": is_readonly_environment(),
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
        "port": os.getenv("PORT", "Not set"),
        "node_env": os.getenv("NODE_ENV", "Not set")
    }

def log_environment_info():
    """Log current environment information"""
    env_info = get_environment_info()
    logger.info(f"🌍 Environment: {env_info['environment']}")
    logger.info(f"🚂 Railway: {env_info['is_railway']}")
    logger.info(f"📝 Read-only: {env_info['is_readonly']}")
    logger.info(f"🔌 Port: {env_info['port']}") 