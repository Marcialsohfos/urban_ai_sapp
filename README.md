# 🏙️ Urban AI - Gestion des Infrastructures Urbaines

Application web pour la gestion intelligente des infrastructures urbaines avec intégration d'IA.

## 🚀 Déploiement sur Hugging Face Spaces

### Prérequis
- Compte [Hugging Face](https://huggingface.co/)
- Fichier Excel avec vos données urbaines

### Installation Locale
```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-username/urban-ai.git
cd urban-ai

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Placer vos données
# Copiez votre fichier Excel dans data/indicateurs_urbains.xlsx

# 4. Configurer l'environnement
cp .env.example .env
# Éditez .env avec vos paramètres

# 5. Lancer l'application
python app.py