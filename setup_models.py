#!/usr/bin/env python3
"""
Script d'initialisation pour Urban AI
Crée la structure de dossiers et initialise les données
"""

import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_project_structure():
    """Crée la structure de dossiers du projet"""
    
    # Déterminer le chemin de base
    if 'RENDER' in os.environ:
        base_dir = Path('/opt/render/project/src')
        logger.info("🚀 Mode Render détecté")
    else:
        base_dir = Path(__file__).parent
        logger.info("💻 Mode développement local")
    
    # Définir les dossiers
    directories = [
        base_dir / 'data',
        base_dir / 'data' / 'uploads',
        base_dir / 'data' / 'uploads' / 'troncons',
        base_dir / 'data' / 'uploads' / 'taudis',
        base_dir / 'models',
        base_dir / 'static',
        base_dir / 'static' / 'css',
        base_dir / 'static' / 'js',
        base_dir / 'static' / 'images',
        base_dir / 'templates',
        base_dir / 'temp'
    ]
    
    # Créer les dossiers
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Créé: {directory}")
    
    # Créer un fichier Excel d'exemple si nécessaire
    excel_path = base_dir / 'data' / 'indicateurs_urbains.xlsx'
    if not excel_path.exists():
        try:
            import pandas as pd
            
            # Données d'exemple
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
            
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)
            logger.info(f"✅ Fichier Excel créé: {excel_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Impossible de créer le fichier Excel: {e}")
            # Créer un fichier texte à la place
            with open(excel_path.with_suffix('.txt'), 'w') as f:
                f.write("Fichier de données indicatives urbaines\n")
                f.write("À remplacer par votre fichier Excel 'indicateurs_urbains.xlsx'\n")
    
    # Créer des fichiers statiques par défaut
    css_file = base_dir / 'static' / 'css' / 'style.css'
    if not css_file.exists():
        css_file.write_text("""
/* Style de base pour Urban AI */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
""")
        logger.info(f"✅ CSS créé: {css_file}")
    
    logger.info("🎉 Structure du projet initialisée avec succès!")
    return base_dir

if __name__ == '__main__':
    base_dir = setup_project_structure()
    print(f"\n📂 Structure créée dans: {base_dir}")
    print("✅ Prêt pour le déploiement!")