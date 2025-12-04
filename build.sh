#!/bin/bash
echo "🔄 Installation des dépendances Python..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "📁 Création des dossiers..."
mkdir -p data/uploads/troncons data/uploads/taudis temp

echo "✅ Build terminé !"