#!/bin/bash
echo "🔄 Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Vérifier la structure
echo "📁 Structure des fichiers :"
ls -la

echo "✅ Build terminé !"