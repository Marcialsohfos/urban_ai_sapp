# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configuration des logs pour Hugging Face"""
    
    # Créer le dossier logs
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                'logs/urban_ai.log',
                maxBytes=10485760,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()  # Pour Hugging Face logs
        ]
    )
    
    return logging.getLogger(__name__)