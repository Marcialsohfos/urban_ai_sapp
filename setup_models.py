import os
import sys
from pathlib import Path

# Gestion des chemins selon l'environnement
if 'RENDER' in os.environ:
    BASE_DIR = Path('/opt/render/project/src')
else:
    BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / 'data'
MODELS_DIR = BASE_DIR / 'models'
STATIC_DIR = BASE_DIR / 'static'
TEMPLATES_DIR = BASE_DIR / 'templates'
TEMP_DIR = BASE_DIR / 'temp'

# Créez les dossiers nécessaires
for dir_path in [DATA_DIR, MODELS_DIR, STATIC_DIR, TEMPLATES_DIR, TEMP_DIR]:
    dir_path.mkdir(exist_ok=True)

print("✅ Structure créée pour Render")