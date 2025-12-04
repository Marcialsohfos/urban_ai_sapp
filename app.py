#!/usr/bin/env python3
"""
Urban AI - Application Flask
"""

import os
import sys
from pathlib import Path

# ==================== CONFIGURATION RENDER ====================
IS_RENDER = 'RENDER' in os.environ

if IS_RENDER:
    BASE_DIR = Path('/opt/render/project/src')
    print("🚀 Mode Render détecté")
else:
    BASE_DIR = Path(__file__).parent

# Ajouter le chemin au sys.path
sys.path.insert(0, str(BASE_DIR))

# ==================== IMPORTS ====================
import secrets
from flask import Flask, jsonify, request, send_from_directory, render_template, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging
import hashlib
from functools import wraps
import pandas as pd
import numpy as np

# ==================== CONFIGURATION ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            static_folder=str(BASE_DIR / 'static'),
            template_folder=str(BASE_DIR / 'templates'))

# Configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', secrets.token_hex(32)),
    PASSWORD_HASH=os.environ.get('PASSWORD_HASH', 
                                 hashlib.sha256('urbankit@1001a'.encode()).hexdigest()),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    UPLOAD_FOLDER=str(BASE_DIR / 'data' / 'uploads'),
    EXCEL_PATH=str(BASE_DIR / 'data' / 'indicateurs_urbains.xlsx')
)

CORS(app)

# ==================== AUTHENTIFICATION ====================
def check_password(password):
    """Vérifie le mot de passe"""
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    return input_hash == app.config['PASSWORD_HASH']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if check_password(password):
            session['logged_in'] = True
            session.permanent = True
            next_page = request.args.get('next', url_for('index'))
            return redirect(next_page)
        return render_template('login.html', error='Mot de passe incorrect')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==================== GESTION DES DONNÉES ====================
class DataManager:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.df = self.load_data()
    
    def load_data(self):
        """Charge les données depuis Excel"""
        try:
            if os.path.exists(self.excel_path):
                df = pd.read_excel(self.excel_path)
                logger.info(f"✅ Données chargées: {len(df)} lignes")
                return df
            else:
                logger.warning("Fichier Excel non trouvé, création de données d'exemple")
                return self.create_sample_data()
        except Exception as e:
            logger.error(f"Erreur chargement: {e}")
            return self.create_sample_data()
    
    def create_sample_data(self):
        """Crée des données d'exemple"""
        data = {
            'Ville': ['Douala', 'Douala', 'Yaoundé', 'Yaoundé'],
            'Nom de la Commune': ['Douala 1', 'Douala 2', 'Yaoundé 1', 'Yaoundé 2'],
            'tronçon de voirie': ['Boulevard 1', 'Rue 2', 'Avenue 3', 'Boulevard 4'],
            'linéaire de voirie(ml)': [2500, 1200, 3200, 1800],
            'Nom de la poche du quartier de taudis': ['Quartier A', 'Quartier B', 'Quartier C', 'Quartier D'],
            'superficie de la poche du quartier de taudis': [12500, 8500, 9800, 7600],
            'présence du nid de poule': ['Oui', 'Non', 'Oui', 'Non'],
            'classe de voirie': ['Primaire', 'Secondaire', 'Primaire', 'Secondaire'],
            'Nombre de point lumineux sur le tronçon': [45, 28, 62, 35]
        }
        return pd.DataFrame(data)
    
    def get_villes(self):
        """Liste des villes"""
        return sorted(self.df['Ville'].dropna().unique().tolist())
    
    def get_communes(self, ville):
        """Communes pour une ville"""
        return sorted(self.df[self.df['Ville'] == ville]['Nom de la Commune'].unique().tolist())

# Initialisation
data_manager = DataManager(app.config['EXCEL_PATH'])

# ==================== ROUTES ====================
@app.route('/')
@login_required
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/api/villes', methods=['GET'])
@login_required
def get_villes():
    """Liste des villes"""
    try:
        villes = data_manager.get_villes()
        return jsonify(villes)
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return jsonify(['Douala', 'Yaoundé'])

@app.route('/api/communes', methods=['GET'])
@login_required
def get_communes():
    """Communes pour une ville"""
    ville = request.args.get('ville')
    if not ville:
        return jsonify({'error': 'Ville requise'}), 400
    communes = data_manager.get_communes(ville)
    return jsonify(communes)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'render': IS_RENDER,
        'data_loaded': len(data_manager.df) > 0
    })

@app.route('/api/upload/image', methods=['POST'])
@login_required
def upload_image():
    """Upload d'image"""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['file']
    image_type = request.form.get('type', 'troncons')
    
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    # Créer le dossier s'il n'existe pas
    upload_dir = Path(app.config['UPLOAD_FOLDER']) / image_type
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    filename = secure_filename(file.filename)
    filepath = upload_dir / filename
    
    try:
        file.save(str(filepath))
        return jsonify({
            'message': 'Image uploadée',
            'filename': filename,
            'url': f'/uploads/{image_type}/{filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<image_type>/<filename>')
def serve_uploaded_image(image_type, filename):
    """Sert les images uploadées"""
    if image_type not in ['troncons', 'taudis']:
        return jsonify({'error': 'Type invalide'}), 400
    
    upload_dir = Path(app.config['UPLOAD_FOLDER']) / image_type
    return send_from_directory(str(upload_dir), filename)

# ==================== DÉMARRAGE ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    print("\n" + "="*50)
    print("🏙️  URBAN AI")
    print("="*50)
    print(f"📁 Base: {BASE_DIR}")
    print(f"🔗 Port: {port}")
    print(f"🌐 URL: http://localhost:{port}")
    print("="*50)
    
    app.run(host='0.0.0.0', port=port, debug=not IS_RENDER)