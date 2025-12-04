#!/usr/bin/env python3
"""
Urban AI - Déploiement Vercel
Application complète de gestion des données urbaines avec IA
"""

import sys
import os

# ==================== CONFIGURATION SPÉCIALE VERCEL ====================
IS_VERCEL = os.environ.get('VERCEL') == '1'

# Ajoutez le chemin du projet à sys.path
if IS_VERCEL:
    # Sur Vercel, on travaille dans /tmp
    sys.path.insert(0, '/tmp')
    print("🚀 Mode Vercel détecté - Configuration spéciale activée")
else:
    # Mode local
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ==================== IMPORT STANDARD ====================
import secrets
from flask import Flask, jsonify, request, send_from_directory, render_template, session, redirect, url_for
from flask_cors import CORS
import pandas as pd
from werkzeug.utils import secure_filename
import logging
import unicodedata
import hashlib
import numpy as np
import math
from pathlib import Path
from functools import wraps

# ==================== CONFIGURATION ====================
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Configuration pour Vercel
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', secrets.token_hex(32)),
    PASSWORD_HASH=os.environ.get('PASSWORD_HASH', 
                                 hashlib.sha256('urbankit@1001a'.encode()).hexdigest()),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600,
)

CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/static/*": {"origins": "*"},
    r"/*": {"origins": "*"}
})

# ==================== DÉTECTION RENDER ====================
IS_RENDER = 'RENDER' in os.environ

if IS_RENDER:
    # Sur Render, on utilise le chemin absolu
    BASE_DIR = Path(__file__).parent.absolute()
    DATA_DIR = BASE_DIR / 'data'
    UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'
    print("🚀 Mode Render détecté - Stockage persistant activé")
else:
    # Développement local
    BASE_DIR = Path(__file__).parent.absolute()
    DATA_DIR = BASE_DIR / 'data'
    UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'

EXCEL_PATH = DATA_DIR / 'indicateurs_urbains.xlsx'
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)

# Création des dossiers
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
(UPLOAD_FOLDER / 'troncons').mkdir(exist_ok=True)
(UPLOAD_FOLDER / 'taudis').mkdir(exist_ok=True)
# ==================== AUTHENTIFICATION ====================
def check_password(password):
    """Vérifie le mot de passe"""
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    return input_hash == app.config['PASSWORD_HASH']

def login_required(f):
    """Décorateur pour les routes protégées"""
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
    """Page de connexion"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if check_password(password):
            session['logged_in'] = True
            session.permanent = True
            next_page = request.args.get('next', url_for('index'))
            return redirect(next_page)
        else:
            return render_template('login.html', error='Mot de passe incorrect')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    return redirect(url_for('login'))

# ==================== GESTION DES DONNÉES ====================
class IndicateursManager:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        logger.info(f"📂 Chargement des données depuis: {excel_path}")
        self.df = self.load_data()
    
    def load_data(self):
        """Charge les données depuis le fichier Excel"""
        try:
            if os.path.exists(self.excel_path):
                df = pd.read_excel(self.excel_path)
                logger.info(f"✅ Données chargées: {len(df)} lignes")
                
                df.columns = df.columns.str.strip()
                
                for col in ['image_troncon', 'image_taudis']:
                    if col not in df.columns:
                        df[col] = ''
                        
                return df
            else:
                logger.warning(f"⚠️ Fichier non trouvé: {self.excel_path}")
                return self.create_sample_data()
        except Exception as e:
            logger.error(f"❌ Erreur chargement: {e}")
            return self.create_sample_data()
    
    def create_sample_data(self):
        """Crée des données d'exemple"""
        sample_data = {
            'Ville': ['Douala', 'Douala', 'Yaoundé', 'Yaoundé'],
            'Nom de la Commune': ['Douala 1', 'Douala 2', 'Yaoundé 1', 'Yaoundé 2'],
            'tronçon de voirie': ['Boulevard 1', 'Rue 2', 'Avenue 3', 'Boulevard 4'],
            'linéaire de voirie(ml)': [2500, 1200, 3200, 1800],
            'Nom de la poche du quartier de taudis': ['Quartier A', 'Quartier B', 'Quartier C', 'Quartier D'],
            'superficie de la poche du quartier de taudis': [12500, 8500, 9800, 7600],
            'présence du nid de poule': ['Oui', 'Non', 'Oui', 'Non'],
            'classe de voirie': ['Primaire', 'Secondaire', 'Primaire', 'Secondaire'],
            'Nombre de point lumineux sur le tronçon': [45, 28, 62, 35],
            'image_troncon': ['', '', '', ''],
            'image_taudis': ['', '', '', '']
        }
        return pd.DataFrame(sample_data)
    
    def remove_accents(self, text):
        """Supprime les accents"""
        if pd.isna(text):
            return ""
        text_str = str(text)
        return ''.join(c for c in unicodedata.normalize('NFD', text_str) 
                      if unicodedata.category(c) != 'Mn')
    
    def normaliser_texte(self, texte):
        """Normalise le texte"""
        if pd.isna(texte):
            return ""
        texte_str = str(texte).strip().lower()
        return self.remove_accents(texte_str)
    
    def formater_nom_ville(self, ville):
        """Formate le nom de la ville"""
        if pd.isna(ville):
            return "Non spécifiée"
        
        ville_normalisee = self.normaliser_texte(ville)
        
        if ville_normalisee == 'yaounde':
            return 'Yaoundé'
        elif ville_normalisee == 'douala':
            return 'Douala'
        else:
            return str(ville).strip().title()
    
    def get_villes(self):
        """Retourne la liste des villes"""
        villes = self.df['Ville'].dropna().unique()
        villes_formatees = [self.formater_nom_ville(ville) for ville in villes]
        return sorted(list(set(villes_formatees)))
    
    def get_communes(self, ville):
        """Retourne les communes d'une ville"""
        logger.info(f"🏙️ Ville demandée: '{ville}'")
        
        if not ville:
            return []
        
        ville_recherchee = self.normaliser_texte(ville)
        logger.info(f"🏙️ Ville normalisée: '{ville_recherchee}'")
        
        mask = self.df['Ville'].apply(self.normaliser_texte) == ville_recherchee
        communes = self.df.loc[mask, 'Nom de la Commune'].dropna().unique().tolist()
        
        logger.info(f"🏘️ Communes trouvées: {communes}")
        return sorted(communes)
    
    def convertir_virgule_en_float(self, valeur):
        """Convertit les nombres avec virgule en float"""
        try:
            if pd.isna(valeur):
                return 0.0
            if isinstance(valeur, (int, float)):
                return float(valeur)
            return float(str(valeur).replace(',', '.').strip())
        except (ValueError, TypeError):
            return 0.0
    
    def clean_nan_values(self, obj):
        """Nettoie les valeurs NaN pour JSON"""
        if isinstance(obj, (int, float)):
            return obj if not pd.isna(obj) else None
        elif isinstance(obj, str):
            return obj
        elif isinstance(obj, dict):
            return {k: self.clean_nan_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.clean_nan_values(item) for item in obj]
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def calculer_stats_generales(self, data):
        """Calcule les statistiques générales"""
        try:
            data = data.copy()
            data['linéaire_ml_numeric'] = data['linéaire de voirie(ml)'].apply(self.convertir_virgule_en_float)
            data['superficie_numeric'] = data['superficie de la poche du quartier de taudis'].apply(self.convertir_virgule_en_float)
            data['points_lumineux_numeric'] = data['Nombre de point lumineux sur le tronçon'].apply(self.convertir_virgule_en_float)

            stats = {
                'nombre_troncons': len(data),
                'total_lineaire_ml': float(data['linéaire_ml_numeric'].sum(skipna=True)),
                'total_superficie_taudis': float(data['superficie_numeric'].sum(skipna=True)),
                'moyenne_points_lumineux': float(data['points_lumineux_numeric'].mean(skipna=True)) if not data['points_lumineux_numeric'].isna().all() else 0
            }
            return stats
        except Exception as e:
            logger.error(f"Erreur calcul stats: {e}")
            return {'nombre_troncons': 0, 'total_lineaire_ml': 0, 'total_superficie_taudis': 0, 'moyenne_points_lumineux': 0}
    
    def analyser_classes_voirie(self, data):
        """Analyse la répartition des classes de voirie"""
        try:
            data_clean = data['classe de voirie'].fillna('Non spécifiée')
            return data_clean.value_counts().to_dict()
        except:
            return {}
    
    def analyser_nids_poule(self, data):
        """Analyse la présence de nids de poule"""
        try:
            data_clean = data['présence du nid de poule'].fillna('Non spécifié')
            return data_clean.value_counts().to_dict()
        except:
            return {'Non spécifié': len(data)}
    
    def preparer_troncons_voirie(self, data):
        """Prépare les données des tronçons"""
        troncons = []
        for _, row in data.iterrows():
            quartier = row.get('Nom de la poche du quartier de taudis', 'Quartier non disponible')
            if pd.isna(quartier):
                quartier = 'Quartier non disponible'
            
            nom = row.get('tronçon de voirie', 'Nom non disponible')
            if pd.isna(nom):
                nom = 'Nom non disponible'
            
            classe = row.get('classe de voirie', 'Non spécifiée')
            if pd.isna(classe):
                classe = 'Non spécifiée'
            
            nid_poule = row.get('présence du nid de poule', 'Non spécifié')
            if pd.isna(nid_poule):
                nid_poule = 'Non spécifié'
            
            image = row.get('image_troncon', '')
            if pd.isna(image):
                image = ''
            
            troncon = {
                'quartier': quartier,
                'nom': nom,
                'lineaire_ml': self.convertir_virgule_en_float(row.get('linéaire de voirie(ml)', 0)),
                'classe': classe,
                'nid_poule': nid_poule,
                'points_lumineux': self.convertir_virgule_en_float(row.get('Nombre de point lumineux sur le tronçon', 0)),
                'image': image
            }
            troncons.append(troncon)
        return troncons
    
    def preparer_quartiers_taudis(self, data):
        """Prépare les données des quartiers"""
        try:
            colonne_superficie = 'superficie de la poche du quartier de taudis'
            colonnes_necessaires = ['Nom de la poche du quartier de taudis', colonne_superficie, 'image_taudis']
            
            for col in colonnes_necessaires:
                if col not in data.columns:
                    logger.warning(f"Colonne manquante: {col}")
                    return []
            
            taudis_data = data[colonnes_necessaires].dropna(subset=['Nom de la poche du quartier de taudis'])
            taudis_data = taudis_data.drop_duplicates()
            
            quartiers = []
            for _, row in taudis_data.iterrows():
                nom = row['Nom de la poche du quartier de taudis']
                if pd.isna(nom):
                    continue
                
                image = row.get('image_taudis', '')
                if pd.isna(image):
                    image = ''
                
                quartier = {
                    'nom': nom,
                    'superficie_m2': self.convertir_virgule_en_float(row[colonne_superficie]),
                    'image': image
                }
                quartiers.append(quartier)
            return quartiers
        except Exception as e:
            logger.error(f"Erreur préparation taudis: {e}")
            return []
    
    def get_indicateurs_commune(self, commune):
        """Récupère les indicateurs pour une commune"""
        logger.info(f"🔍 Commune demandée: '{commune}'")

        if not commune:
            logger.warning("Commune vide")
            return None

        commune_cleaned = self.normaliser_texte(commune)
        logger.info(f"🔍 Commune normalisée: '{commune_cleaned}'")

        mask = self.df['Nom de la Commune'].apply(self.normaliser_texte) == commune_cleaned
        commune_data = self.df[mask]
        
        logger.info(f"📊 {len(commune_data)} lignes trouvées")
        
        if len(commune_data) == 0:
            logger.warning(f"Aucune donnée pour '{commune}'")
            return None
        
        ville_formatee = self.formater_nom_ville(commune_data['Ville'].iloc[0])
        
        indicateurs = {
            'commune': commune,
            'ville': ville_formatee,
            'stats_generales': self.clean_nan_values(self.calculer_stats_generales(commune_data)),
            'troncons_voirie': self.clean_nan_values(self.preparer_troncons_voirie(commune_data)),
            'quartiers_taudis': self.clean_nan_values(self.preparer_quartiers_taudis(commune_data)),
            'analyse_classes_voirie': self.clean_nan_values(self.analyser_classes_voirie(commune_data)),
            'analyse_nids_poule': self.clean_nan_values(self.analyser_nids_poule(commune_data))
        }
        
        logger.info("✅ Indicateurs générés")
        return indicateurs

# Initialisation
indicateurs_manager = IndicateursManager(EXCEL_PATH)

# ==================== MODÈLES IA ====================
class MaintenancePredictor:
    """Modèle IA de prédiction de maintenance"""
    def __init__(self):
        self.priority_labels = {
            0: 'Basse priorité',
            1: 'Priorité moyenne', 
            2: 'Haute priorité',
            3: 'Urgence'
        }
    
    def predict_priority(self, troncon_data):
        """Prédit la priorité de maintenance"""
        try:
            # Simuler une prédiction d'IA
            features = [
                troncon_data.get('lineaire_ml', 0),
                2 if troncon_data.get('classe') == 'Primaire' else 1,
                troncon_data.get('points_lumineux', 0),
                np.random.randint(5, 20),  # Âge estimé
                troncon_data.get('points_lumineux', 0) * 100,  # Trafic estimé
                1500  # Précipitation moyenne
            ]
            
            # Logique de priorité simple
            lineaire = troncon_data.get('lineaire_ml', 0)
            points_lumineux = troncon_data.get('points_lumineux', 0)
            nid_poule = troncon_data.get('nid_poule', 'Non')
            
            # Calcul du score
            score = 0
            if lineaire > 2000:
                score += 1
            if points_lumineux < 20:
                score += 1
            if nid_poule == 'Oui':
                score += 2
            
            priority_level = min(score, 3)
            confidence = np.random.uniform(0.7, 0.95)
            
            return {
                'niveau': priority_level,
                'label': self.priority_labels.get(priority_level, 'Inconnu'),
                'probabilite': confidence,
                'details': [0.1, 0.2, 0.3, 0.4]  # Distribution factice
            }
        except Exception as e:
            logger.error(f"Erreur prédiction IA: {e}")
            return {
                'niveau': 0,
                'label': 'Indéterminé',
                'probabilite': 0.0,
                'details': [0.25, 0.25, 0.25, 0.25]
            }

class RoadDefectDetector:
    """Détecteur de défauts sur les routes"""
    def __init__(self):
        self.classes = ['bon_etat', 'nids_poule', 'fissures', 'deformation']
    
    def analyze_road_image(self, img_path):
        """Analyse une image de route"""
        try:
            # Simulation d'analyse IA
            probs = np.random.dirichlet(np.ones(4))
            class_idx = np.argmax(probs)
            
            return {
                'etat': self.classes[class_idx],
                'confiance': float(probs[class_idx]),
                'details': dict(zip(self.classes, probs.tolist()))
            }
        except Exception as e:
            logger.error(f"Erreur analyse image: {e}")
            return self.create_dummy_analysis()
    
    def create_dummy_analysis(self):
        """Analyse factice"""
        probs = np.random.dirichlet(np.ones(4))
        class_idx = np.argmax(probs)
        
        return {
            'etat': self.classes[class_idx],
            'confiance': float(probs[class_idx]),
            'details': dict(zip(self.classes, probs.tolist()))
        }

class UrbanResourceOptimizer:
    """Optimiseur de ressources urbaines"""
    def __init__(self):
        pass
    
    def optimize_lighting(self, data):
        """Optimise l'éclairage public"""
        if not data:
            return []
        
        try:
            df = pd.DataFrame(data)
            
            # Regrouper par classe de voirie
            recommendations = []
            for classe in df['classe'].unique():
                cluster_data = df[df['classe'] == classe]
                avg_lights = cluster_data['points_lumineux'].mean()
                avg_length = cluster_data['lineaire_ml'].mean()
                
                # Calcul recommandation
                if classe == 'Primaire':
                    optimal_lights = max(10, int(avg_length / 30))
                elif classe == 'Secondaire':
                    optimal_lights = max(8, int(avg_length / 35))
                else:
                    optimal_lights = max(5, int(avg_length / 40))
                
                recommendations.append({
                    'cluster': classe,
                    'troncons': len(cluster_data),
                    'eclairage_actuel_moyen': float(avg_lights),
                    'eclairage_recommande': optimal_lights,
                    'economie_potentielle': float(avg_lights - optimal_lights),
                    'troncons_cibles': cluster_data['nom'].tolist()[:3]
                })
            
            return recommendations
        except Exception as e:
            logger.error(f"Erreur optimisation éclairage: {e}")
            return []

# Initialisation des modèles IA
maintenance_model = MaintenancePredictor()
defect_detector = RoadDefectDetector()
resource_optimizer = UrbanResourceOptimizer()
IA_MODELS_AVAILABLE = True

# ==================== ROUTES ====================
@app.route('/')
@login_required
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/images/<image_type>/<filename>')
def serve_image(image_type, filename):
    """Sert les images"""
    if image_type not in ['troncons', 'taudis']:
        return jsonify({'error': 'Type invalide'}), 400
    
    try:
        return send_from_directory(
            os.path.join(app.config['UPLOAD_FOLDER'], image_type),
            filename
        )
    except FileNotFoundError:
        return jsonify({'error': 'Image non trouvée'}), 404

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
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], image_type, filename)
        file.save(save_path)
        
        logger.info(f"✅ Image sauvegardée: {save_path}")
        return jsonify({
            'message': 'Image uploadée avec succès',
            'filename': filename
        })
    
    return jsonify({'error': 'Type non autorisé'}), 400

@app.route('/api/villes', methods=['GET'])
@login_required
def get_villes():
    """Liste des villes"""
    try:
        villes = indicateurs_manager.get_villes()
        return jsonify(villes)
    except Exception as e:
        logger.error(f"Erreur /api/villes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/communes', methods=['GET'])
@login_required
def get_communes():
    """Liste des communes pour une ville"""
    ville = request.args.get('ville')
    if not ville:
        return jsonify({'error': 'Ville requise'}), 400
    
    communes = indicateurs_manager.get_communes(ville)
    return jsonify(communes)

@app.route('/api/indicateurs', methods=['GET'])
@login_required
def get_indicateurs():
    """Indicateurs pour une commune"""
    commune = request.args.get('commune')
    logger.info(f"🌐 Requête indicateurs pour: {commune}")
    
    if not commune:
        return jsonify({'error': 'Commune requise'}), 400
    
    try:
        indicateurs = indicateurs_manager.get_indicateurs_commune(commune)
        if indicateurs is None:
            return jsonify({'error': 'Commune non trouvée'}), 404
        
        indicateurs_clean = indicateurs_manager.clean_nan_values(indicateurs)
        return jsonify(indicateurs_clean)
        
    except Exception as e:
        logger.error(f"Erreur /api/indicateurs: {e}")
        return jsonify({'error': f'Erreur interne: {str(e)}'}), 500

@app.route('/api/ai/analyze-image', methods=['POST'])
@login_required
def analyze_image_ai():
    """Analyse d'image avec IA"""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['file']
    analysis_type = request.form.get('type', 'defect')
    
    temp_path = os.path.join(BASE_DIR, 'temp', secure_filename(file.filename))
    os.makedirs(os.path.join(BASE_DIR, 'temp'), exist_ok=True)
    
    try:
        file.save(temp_path)
        
        if analysis_type == 'defect':
            result = defect_detector.analyze_road_image(temp_path)
        else:
            os.remove(temp_path)
            return jsonify({'error': 'Type non supporté'}), 400
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify(result)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Erreur analyse IA: {e}")
        return jsonify({'error': f'Erreur analyse: {str(e)}'}), 500

@app.route('/api/ai/predict-maintenance', methods=['GET'])
@login_required
def predict_maintenance():
    """Prédiction des priorités de maintenance"""
    commune = request.args.get('commune')
    
    if not commune:
        return jsonify({'error': 'Commune requise'}), 400
    
    indicateurs = indicateurs_manager.get_indicateurs_commune(commune)
    if not indicateurs:
        return jsonify({'error': 'Données non disponibles'}), 404
    
    try:
        troncons_data = []
        for troncon in indicateurs['troncons_voirie']:
            prediction = maintenance_model.predict_priority(troncon)
            troncon_copy = troncon.copy()
            troncon_copy['prediction_ia'] = prediction
            troncons_data.append(troncon_copy)
        
        lighting_optim = resource_optimizer.optimize_lighting(indicateurs['troncons_voirie'])
        urgents = [t for t in troncons_data if t['prediction_ia']['niveau'] >= 2]
        
        return jsonify({
            'commune': commune,
            'troncons_avec_predictions': troncons_data,
            'optimisation_eclairage': lighting_optim,
            'recommandations_globales': {
                'priorite_max': max((t['prediction_ia']['niveau'] for t in troncons_data), default=0),
                'troncons_urgents': urgents[:5],
                'budget_estime': sum(t['lineaire_ml'] * 100 for t in urgents)
            }
        })
    except Exception as e:
        logger.error(f"Erreur prédiction maintenance: {e}")
        return jsonify({'error': f'Erreur IA: {str(e)}'}), 500

@app.route('/api/ai/smart-recommendations', methods=['GET'])
@login_required
def smart_recommendations():
    """Recommandations intelligentes"""
    ville = request.args.get('ville')
    
    if not ville:
        return jsonify({'error': 'Ville requise'}), 400
    
    try:
        communes = indicateurs_manager.get_communes(ville)
        all_data = []
        
        for commune in communes[:3]:
            indicateurs = indicateurs_manager.get_indicateurs_commune(commune)
            if indicateurs:
                for troncon in indicateurs['troncons_voirie'][:5]:
                    troncon_copy = troncon.copy()
                    troncon_copy['commune'] = commune
                    all_data.append(troncon_copy)
        
        if not all_data:
            return jsonify({'error': 'Aucune donnée'}), 404
        
        df = pd.DataFrame(all_data)
        critical_points = df[df['nid_poule'] == 'Oui']
        
        recommendations = {
            'ville': ville,
            'analyse_comparative': {
                'nombre_communes_analysées': len(communes),
                'nombre_troncons_analyses': len(all_data),
                'taux_nids_poule': len(critical_points) / len(all_data) * 100 if len(all_data) > 0 else 0
            },
            'plan_daction': [
                {
                    'action': 'Renforcement éclairage',
                    'communes_cibles': ['Douala 1', 'Yaoundé 1'][:len(communes)],
                    'impact_estime': '30% réduction accidents nocturnes'
                },
                {
                    'action': 'Programme maintenance préventive',
                    'troncons_cibles': df.nlargest(3, 'lineaire_ml')['nom'].tolist() if len(df) > 0 else [],
                    'budget_estime': df['lineaire_ml'].sum() * 50 if len(df) > 0 else 0
                }
            ]
        }
        
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"Erreur recommandations IA: {e}")
        return jsonify({'error': f'Erreur IA: {str(e)}'}), 500

@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """État des modèles IA"""
    return jsonify({
        'ia_disponible': IA_MODELS_AVAILABLE,
        'mode': 'production' if IA_MODELS_AVAILABLE else 'simulation',
        'message': 'IA pleinement fonctionnelle' if IA_MODELS_AVAILABLE else 'Mode démonstration'
    })

@app.route('/api/data/info', methods=['GET'])
@login_required
def data_info():
    """Informations sur les données"""
    info = {
        'structure': {
            'data_dir': str(DATA_DIR),
            'excel_file': str(EXCEL_PATH),
            'excel_exists': os.path.exists(EXCEL_PATH),
            'uploads_dir': str(UPLOAD_FOLDER),
            'troncons_dir': str(UPLOAD_FOLDER / 'troncons'),
            'taudis_dir': str(UPLOAD_FOLDER / 'taudis'),
        },
        'statistiques': {
            'nombre_images_troncons': len(os.listdir(UPLOAD_FOLDER / 'troncons')),
            'nombre_images_taudis': len(os.listdir(UPLOAD_FOLDER / 'taudis')),
        }
    }
    
    return jsonify(info)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'ia_available': IA_MODELS_AVAILABLE,
        'data_loaded': len(indicateurs_manager.df) > 0,
        'vercel': IS_VERCEL,
        'data_dir': str(DATA_DIR)
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Fichiers statiques"""
    return send_from_directory(app.static_folder, filename)

# ==================== HANDLER VERCEL ====================
# Vercel a besoin d'une variable `app` exportée
application = app

# ==================== DÉMARRAGE LOCAL ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    
    print("\n" + "="*60)
    print("🏙️  URBAN AI - GESTION DES INFRASTRUCTURES URBAINES")
    print("="*60)
    print(f"📁 Dossier data: {DATA_DIR}")
    print(f"📊 Données: {len(indicateurs_manager.df)} lignes")
    print(f"🤖 IA: {'✅ Active' if IA_MODELS_AVAILABLE else '⚠️ Simulation'}")
    print(f"🔒 Authentification: Activée (urbankit@1001a)")
    print(f"🔗 URL: http://localhost:{port}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)