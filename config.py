"""
Configuration pour Urban AI avec structure data/uploads/
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de base"""
    
    # Chemins (MIS À JOUR)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')  # Dossier data principal
    EXCEL_PATH = os.path.join(DATA_DIR, 'indicateurs_urbains.xlsx')
    UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')  # MODIFIÉ ICI
    
    # Sécurité
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    PASSWORD = os.environ.get('APP_PASSWORD', 'urbankit@1001a')
    
    # Application
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # IA
    AI_MODELS_DIR = os.path.join(BASE_DIR, 'models')
    
    @staticmethod
    def init_directories():
        """Initialise les répertoires nécessaires"""
        directories = [
            Config.DATA_DIR,
            Config.UPLOAD_DIR,
            os.path.join(Config.UPLOAD_DIR, 'troncons'),
            os.path.join(Config.UPLOAD_DIR, 'taudis'),
            Config.AI_MODELS_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Répertoire créé/validé: {directory}")
    
    @staticmethod
    def get_password_hash():
        """Retourne le hash du mot de passe"""
        import hashlib
        return hashlib.sha256(Config.PASSWORD.encode()).hexdigest()
    
    @staticmethod
    def get_upload_path(image_type, filename):
        """
        Retourne le chemin complet pour une image
        image_type: 'troncons' ou 'taudis'
        filename: nom du fichier
        """
        return os.path.join(Config.UPLOAD_DIR, image_type, filename)