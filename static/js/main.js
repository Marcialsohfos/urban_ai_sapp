/**
 * Urban AI - Application de Gestion des Infrastructures Urbaines
 * Script JavaScript principal
 * Version : 2.0.0
 */

// ==================== CONFIGURATION ====================
class UrbanAIConfig {
    constructor() {
        this.apiBaseUrl = this.getApiBaseUrl();
        this.imageBaseUrl = this.getImageBaseUrl();
        this.currentCommune = null;
        this.currentData = null;
        this.imageAnalysisMode = false;
        this.aiStatus = null;
        
        // NOUVEAU : Information sur la structure de données
        this.dataStructure = {
            base: '/data',
            uploads: '/data/uploads',
            troncons: '/data/uploads/troncons',
            taudis: '/data/uploads/taudis'
        };
        
        this.init();
    }
    
    getApiBaseUrl() {
        const host = window.location.hostname;
        
        if (host === 'localhost' || host === '127.0.0.1') {
            return 'http://127.0.0.1:5000/api';
        } else if (window.location.href.includes('huggingface.co')) {
            return window.location.origin + '/api';
        } else {
            return '/api';
        }
    }
    
    getImageBaseUrl() {
        const host = window.location.hostname;
        
        if (host === 'localhost' || host === '127.0.0.1') {
            return 'http://127.0.0.1:5000/images';
        } else if (window.location.href.includes('huggingface.co')) {
            return window.location.origin + '/images';
        } else {
            return '/images';
        }
    }
    
    async getDataInfo() {
        // NOUVEAU : Récupérer les infos sur la structure de données
        try {
            const response = await fetch(`${this.apiBaseUrl}/data/info`);
            if (response.ok) {
                const data = await response.json();
                console.log('📊 Structure de données:', data);
                return data;
            }
        } catch (error) {
            console.warn('Impossible de récupérer les infos données:', error);
        }
        return null;
    }
    
    init() {
        console.log('🌐 Urban AI - Configuration initialisée');
        console.log('📡 API URL:', this.apiBaseUrl);
        console.log('🖼️ Image URL:', this.imageBaseUrl);
        
        // Tester la connexion
        this.testConnection();
        
        // Vérifier l'état de l'IA
        this.checkAIStatus();
    }
    
    async testConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            console.log('✅ Connexion API établie:', data);
        } catch (error) {
            console.error('❌ Erreur de connexion:', error);
            this.showNotification('Impossible de se connecter au serveur', 'error');
        }
    }
    
    async checkAIStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/ai/status`);
            const data = await response.json();
            this.aiStatus = data;
            
            if (data.ia_disponible) {
                console.log('🤖 IA disponible:', data);
            } else {
                console.warn('⚠️ IA en mode simulation');
            }
        } catch (error) {
            console.error('Erreur vérification IA:', error);
        }
    }
}

// ==================== GESTION DES DONNÉES ====================
class DataManager {
    constructor(config) {
        this.config = config;
        this.villes = [];
        this.communes = [];
    }
    
    async loadVilles() {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/villes`);
            if (!response.ok) throw new Error('Erreur réseau');
            
            this.villes = await response.json();
            return this.villes;
        } catch (error) {
            console.error('Erreur chargement villes:', error);
            throw error;
        }
    }
    
    async loadCommunes(ville) {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/communes?ville=${encodeURIComponent(ville)}`);
            if (!response.ok) throw new Error('Erreur réseau');
            
            this.communes = await response.json();
            return this.communes;
        } catch (error) {
            console.error('Erreur chargement communes:', error);
            throw error;
        }
    }
    
    async loadIndicateurs(commune) {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/indicateurs?commune=${encodeURIComponent(commune)}`);
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Commune non trouvée');
                }
                throw new Error('Erreur serveur');
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.config.currentCommune = commune;
            this.config.currentData = data;
            
            return data;
        } catch (error) {
            console.error('Erreur chargement indicateurs:', error);
            throw error;
        }
    }
}

// ==================== GESTION DE L'INTERFACE ====================
class UIManager {
    constructor(config, dataManager) {
        this.config = config;
        this.dataManager = dataManager;
        
        // Éléments DOM
        this.elements = {
            villeSelect: document.getElementById('villeSelect'),
            communeSelect: document.getElementById('communeSelect'),
            resetBtn: document.getElementById('resetBtn'),
            loading: document.getElementById('loading'),
            errorContainer: document.getElementById('errorContainer'),
            errorMessage: document.getElementById('errorMessage'),
            indicatorsContainer: document.getElementById('indicatorsContainer'),
            tronconsGallery: document.getElementById('tronconsGallery'),
            taudisGallery: document.getElementById('taudisGallery'),
            aiPriorityScore: document.getElementById('aiPriorityScore'),
            aiRecommendations: document.getElementById('aiRecommendations'),
            aiStatusMessage: document.getElementById('aiStatusMessage'),
            aiStatsContent: document.getElementById('aiStatsContent'),
            aiPredictionsBody: document.getElementById('aiPredictionsBody')
        };
        
        this.svgNoImage = this.createNoImageSVG();
        this.initEventListeners();
    }
    
    createNoImageSVG() {
        return `data:image/svg+xml;base64,${btoa(`
            <svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#f8f9fa"/>
                <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" 
                      fill="#6c757d" font-family="Arial" font-size="14">
                    Image non disponible
                </text>
            </svg>
        `)}`;
    }
    
    initEventListeners() {
        // Chargement des communes quand la ville change
        this.elements.villeSelect.addEventListener('change', async () => {
            const selectedVille = this.elements.villeSelect.value;
            
            if (!selectedVille) {
                this.resetCommuneSelect();
                return;
            }
            
            this.elements.communeSelect.disabled = true;
            this.elements.communeSelect.innerHTML = '<option value="">Chargement...</option>';
            
            try {
                const communes = await this.dataManager.loadCommunes(selectedVille);
                this.populateCommuneSelect(communes);
                this.elements.communeSelect.disabled = false;
            } catch (error) {
                this.elements.communeSelect.innerHTML = '<option value="">Erreur de chargement</option>';
                this.showError('Impossible de charger les communes');
            }
        });
        
        // Chargement des indicateurs quand la commune change
        this.elements.communeSelect.addEventListener('change', async () => {
            const commune = this.elements.communeSelect.value;
            
            if (!commune) return;
            
            this.showLoading();
            this.hideError();
            this.hideIndicators();
            
            try {
                const indicateurs = await this.dataManager.loadIndicateurs(commune);
                this.displayIndicateurs(indicateurs);
                this.hideLoading();
                this.showIndicators();
            } catch (error) {
                this.hideLoading();
                this.showError(`Impossible de charger les données: ${error.message}`);
            }
        });
        
        // Réinitialisation
        this.elements.resetBtn.addEventListener('click', () => {
            this.resetUI();
        });
    }
    
    populateVilleSelect(villes) {
        this.elements.villeSelect.innerHTML = '<option value="">Sélectionnez une ville</option>';
        
        villes.forEach(ville => {
            const option = document.createElement('option');
            option.value = ville;
            option.textContent = ville;
            this.elements.villeSelect.appendChild(option);
        });
    }
    
    populateCommuneSelect(communes) {
        this.elements.communeSelect.innerHTML = '<option value="">Sélectionnez une commune</option>';
        
        communes.forEach(commune => {
            const option = document.createElement('option');
            option.value = commune;
            option.textContent = commune.replace('Yaounde', 'Yaoundé');
            this.elements.communeSelect.appendChild(option);
        });
    }
    
    resetCommuneSelect() {
        this.elements.communeSelect.innerHTML = '<option value="">Sélectionnez d\'abord une ville</option>';
        this.elements.communeSelect.disabled = true;
    }
    
    resetUI() {
        this.elements.villeSelect.value = '';
        this.resetCommuneSelect();
        this.hideIndicators();
        this.hideError();
        this.config.currentCommune = null;
        this.config.currentData = null;
    }
    
    showLoading() {
        this.elements.loading.classList.remove('d-none');
    }
    
    hideLoading() {
        this.elements.loading.classList.add('d-none');
    }
    
    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorContainer.classList.remove('d-none');
    }
    
    hideError() {
        this.elements.errorContainer.classList.add('d-none');
    }
    
    showIndicators() {
        this.elements.indicatorsContainer.classList.remove('d-none');
    }
    
    hideIndicators() {
        this.elements.indicatorsContainer.classList.add('d-none');
    }
    
    showNotification(message, type = 'info') {
        // Créer une notification temporaire
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Supprimer automatiquement après 5 secondes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// ==================== GESTION DES IMAGES ====================
class ImageManager {
    constructor(config) {
        this.config = config;
        this.modalImage = document.getElementById('modalImage');
        this.aiAnalyzeImage = document.getElementById('aiAnalyzeImage');
        this.aiAnalysisResults = document.getElementById('aiAnalysisResults');
    }
    
    createImageCard(imageData, imageType, extraInfo = '') {
        const hasImage = imageData.image && imageData.image.trim() !== '';
        const imageUrl = hasImage 
            ? `${this.config.imageBaseUrl}/${imageType}/${encodeURIComponent(imageData.image)}`
            : this.svgNoImage;
        
        const title = imageData.nom || 'Sans nom';
        const description = this.getImageDescription(imageData, imageType);
        
        const card = document.createElement('div');
        card.className = 'image-card ai-result-item';
        card.innerHTML = `
            <div class="card h-100">
                <div style="height: 150px; overflow: hidden; cursor: pointer;" 
                     onclick="${hasImage ? `urbanAI.openImageModal('${imageUrl}', '${title.replace(/'/g, "\\'")}')` : ''}">
                    <img src="${imageUrl}" class="card-img-top" alt="${title}" 
                         style="width: 100%; height: 100%; object-fit: ${hasImage ? 'cover' : 'contain'};"
                         onerror="this.src='${this.svgNoImage}'">
                    ${extraInfo ? `<div class="position-absolute top-0 end-0 m-2">${extraInfo}</div>` : ''}
                </div>
                <div class="card-body">
                    <h6 class="card-title">${title}</h6>
                    <small class="text-muted">${description}</small>
                    ${hasImage && this.config.imageAnalysisMode ? `
                        <div class="mt-2">
                            <button class="btn btn-sm btn-outline-primary w-100" 
                                    onclick="urbanAI.analyzeImage('${imageUrl}', '${title.replace(/'/g, "\\'")}', '${imageType}')">
                                <i class="fas fa-robot"></i> Analyser IA
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        return card;
    }
    
    getImageDescription(imageData, imageType) {
        if (imageType === 'troncons') {
            return `Linéaire: ${imageData.lineaire_ml}m | Classe: ${imageData.classe}`;
        } else if (imageType === 'taudis') {
            return `Superficie: ${imageData.superficie_m2}m²`;
        }
        return '';
    }
    
    displayTronconsGallery(troncons) {
        const gallery = document.getElementById('tronconsGallery');
        gallery.innerHTML = '';
        
        if (!troncons || troncons.length === 0) {
            gallery.innerHTML = '<p class="text-muted">Aucun tronçon disponible</p>';
            return;
        }
        
        troncons.forEach(troncon => {
            const priorityBadge = troncon.prediction_ia ? 
                `<span class="badge priority-${troncon.prediction_ia.niveau}">${troncon.prediction_ia.label}</span>` : '';
            
            const card = this.createImageCard(troncon, 'troncons', priorityBadge);
            gallery.appendChild(card);
        });
    }
    
    displayTaudisGallery(taudis) {
        const gallery = document.getElementById('taudisGallery');
        gallery.innerHTML = '';
        
        if (!taudis || taudis.length === 0) {
            gallery.innerHTML = '<p class="text-muted">Aucun quartier disponible</p>';
            return;
        }
        
        taudis.forEach(taudis => {
            const card = this.createImageCard(taudis, 'taudis');
            gallery.appendChild(card);
        });
    }
    
    openImageModal(imageUrl, title) {
        if (imageUrl === this.svgNoImage) return;
        
        this.modalImage.src = imageUrl;
        this.modalImage.dataset.title = title;
        this.modalImage.dataset.url = imageUrl;
        
        const modal = new bootstrap.Modal(document.getElementById('imageModal'));
        modal.show();
    }
    
    async analyzeImage(imageUrl, title, imageType) {
        try {
            // Télécharger l'image
            const response = await fetch(imageUrl);
            const blob = await response.blob();
            
            // Préparer FormData
            const formData = new FormData();
            formData.append('file', blob, `${title}.jpg`);
            formData.append('type', 'defect');
            
            // Envoyer à l'API
            const aiResponse = await fetch(`${this.config.apiBaseUrl}/ai/analyze-image`, {
                method: 'POST',
                body: formData
            });
            
            if (!aiResponse.ok) throw new Error('Erreur analyse IA');
            
            const result = await aiResponse.json();
            this.displayImageAnalysis(result, imageUrl, title);
            
        } catch (error) {
            console.error('Erreur analyse image:', error);
            this.showNotification('Erreur lors de l\'analyse IA', 'error');
        }
    }
    
    displayImageAnalysis(result, imageUrl, title) {
        const modal = document.getElementById('aiImageModal');
        const modalImage = document.getElementById('aiAnalyzeImage');
        const resultsDiv = document.getElementById('aiAnalysisResults');
        
        modalImage.src = imageUrl;
        
        let resultsHTML = `
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5 class="card-title mb-0">Résultats de l'analyse IA</h5>
                </div>
                <div class="card-body">
                    <h6>État détecté: 
                        <span class="badge ${result.etat === 'bon_etat' ? 'bg-success' : 'bg-danger'}">
                            ${result.etat.replace('_', ' ').toUpperCase()}
                        </span>
                    </h6>
                    <p>Confiance: <strong>${(result.confiance * 100).toFixed(1)}%</strong></p>
                    
                    <h6 class="mt-3">Distribution des probabilités:</h6>
                    <div class="list-group">`;
        
        Object.entries(result.details).forEach(([key, value]) => {
            const percentage = (value * 100).toFixed(1);
            resultsHTML += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span>${key.replace('_', ' ')}</span>
                    <div class="d-flex align-items-center">
                        <div class="progress me-2" style="width: 100px; height: 10px;">
                            <div class="progress-bar" role="progressbar" 
                                 style="width: ${percentage}%"></div>
                        </div>
                        <span class="badge bg-primary rounded-pill">${percentage}%</span>
                    </div>
                </div>`;
        });
        
        resultsHTML += `
                    </div>
                    
                    <div class="mt-3">
                        <h6>Recommandation:</h6>
                        <div class="alert ${result.etat === 'bon_etat' ? 'alert-success' : 'alert-warning'}">
                            ${this.getImageRecommendation(result.etat)}
                        </div>
                    </div>
                </div>
            </div>`;
        
        resultsDiv.innerHTML = resultsHTML;
        new bootstrap.Modal(modal).show();
    }
    
    getImageRecommendation(etat) {
        const recommendations = {
            'bon_etat': '✅ Aucune action nécessaire. Maintenance préventive recommandée.',
            'nids_poule': '⚠️ Nids de poule détectés. Réparation urgente recommandée.',
            'fissures': '⚠️ Fissures détectées. Inspection approfondie nécessaire.',
            'deformation': '🚨 Déformation de la chaussée. Intervention immédiate requise.'
        };
        
        return recommendations[etat] || '❓ Analyse incomplète. Nouvelle analyse recommandée.';
    }
}

// ==================== GESTION DE L'IA ====================
class AIManager {
    constructor(config) {
        this.config = config;
    }
    
    async getAIRecommendations(commune) {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/ai/predict-maintenance?commune=${encodeURIComponent(commune)}`);
            
            if (!response.ok) {
                if (response.status === 503) {
                    throw new Error('Service IA temporairement indisponible');
                }
                throw new Error('Erreur serveur IA');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Erreur recommandations IA:', error);
            throw error;
        }
    }
    
    async getSmartRecommendations(ville) {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/ai/smart-recommendations?ville=${encodeURIComponent(ville)}`);
            
            if (!response.ok) throw new Error('Erreur recommandations intelligentes');
            
            return await response.json();
        } catch (error) {
            console.error('Erreur recommandations intelligentes:', error);
            throw error;
        }
    }
    
    displayAIRecommendations(data) {
        const container = document.getElementById('aiRecommendations');
        
        if (!data) {
            container.innerHTML = '<div class="alert alert-warning">Aucune donnée IA disponible</div>';
            return;
        }
        
        let html = `
            <div class="alert alert-info ai-result-item">
                <h5><i class="fas fa-robot"></i> Analyse IA pour ${data.commune}</h5>
                <p><strong>${data.troncons_avec_predictions?.length || 0}</strong> tronçons analysés</p>
            </div>`;
        
        // Optimisation de l'éclairage
        if (data.optimisation_eclairage?.length > 0) {
            html += this.createLightingOptimizationTable(data.optimisation_eclairage);
        }
        
        // Tronçons urgents
        if (data.recommandations_globales?.troncons_urgents?.length > 0) {
            html += this.createUrgentTronconsSection(data.recommandations_globales);
        }
        
        container.innerHTML = html;
    }
    
    createLightingOptimizationTable(optimizationData) {
        let html = `
            <div class="ai-result-item">
                <h6><i class="fas fa-lightbulb"></i> Optimisation de l'éclairage</h6>
                <div class="table-responsive">
                    <table class="table table-sm table-hover">
                        <thead>
                            <tr>
                                <th>Groupe</th>
                                <th>Tronçons</th>
                                <th>Éclairage actuel</th>
                                <th>Recommandé</th>
                                <th>Économie potentielle</th>
                            </tr>
                        </thead>
                        <tbody>`;
        
        optimizationData.forEach(opt => {
            const economyClass = opt.economie_potentielle > 0 ? 'text-success' : 'text-danger';
            html += `
                <tr>
                    <td><span class="badge bg-secondary">Groupe ${opt.cluster}</span></td>
                    <td>${opt.troncons}</td>
                    <td>${opt.eclairage_actuel_moyen.toFixed(1)} points</td>
                    <td>${opt.eclairage_recommande} points</td>
                    <td class="${economyClass} fw-bold">
                        ${opt.economie_potentielle > 0 ? '+' : ''}${opt.economie_potentielle.toFixed(1)} points
                    </td>
                </tr>`;
        });
        
        html += `</tbody></table></div></div>`;
        return html;
    }
    
    createUrgentTronconsSection(recommandations) {
        let html = `
            <div class="alert alert-warning ai-result-item mt-3">
                <h6><i class="fas fa-exclamation-triangle"></i> Tronçons nécessitant une attention immédiate</h6>
                <ul class="mb-0">`;
        
        recommandations.troncons_urgents.slice(0, 5).forEach(t => {
            html += `
                <li>
                    <strong>${t.nom}</strong> - 
                    Priorité: <span class="badge priority-${t.prediction_ia.niveau}">${t.prediction_ia.label}</span> -
                    Confiance: ${(t.prediction_ia.probabilite * 100).toFixed(1)}%
                </li>`;
        });
        
        if (recommandations.budget_estime > 0) {
            html += `
                <li class="mt-2">
                    <strong>Budget estimé:</strong> ${recommandations.budget_estime.toLocaleString()} FCFA
                </li>`;
        }
        
        html += `</ul></div>`;
        return html;
    }
    
    updatePriorityScore(data) {
        const scoreElement = document.getElementById('aiPriorityScore');
        
        if (!data || !data.recommandations_globales) {
            scoreElement.textContent = '--';
            return;
        }
        
        const urgents = data.recommandations_globales.troncons_urgents || [];
        
        if (urgents.length > 0) {
            const avgPriority = data.recommandations_globales.priorite_max * 25;
            const score = Math.min(100, avgPriority + 20);
            
            scoreElement.textContent = score;
            
            if (score > 70) {
                scoreElement.className = 'display-4 text-danger';
            } else if (score > 40) {
                scoreElement.className = 'display-4 text-warning';
            } else {
                scoreElement.className = 'display-4 text-success';
            }
        } else {
            scoreElement.textContent = '25';
            scoreElement.className = 'display-4 text-success';
        }
    }
    
    displayAIPredictions(data) {
        const section = document.getElementById('aiPredictionsSection');
        const tableBody = document.getElementById('aiPredictionsBody');
        
        if (!data || !data.troncons_avec_predictions) {
            section.style.display = 'none';
            return;
        }
        
        tableBody.innerHTML = '';
        
        data.troncons_avec_predictions.forEach(troncon => {
            const row = document.createElement('tr');
            row.className = 'ai-result-item';
            
            row.innerHTML = `
                <td>${troncon.nom}</td>
                <td><span class="badge bg-info">${troncon.classe}</span></td>
                <td>${troncon.lineaire_ml.toLocaleString()} m</td>
                <td>
                    <span class="badge priority-${troncon.prediction_ia.niveau}">
                        ${troncon.prediction_ia.label}
                    </span>
                </td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar ${this.getPriorityColor(troncon.prediction_ia.niveau)}" 
                             role="progressbar" 
                             style="width: ${troncon.prediction_ia.probabilite * 100}%">
                            ${(troncon.prediction_ia.probabilite * 100).toFixed(1)}%
                        </div>
                    </div>
                </td>
                <td>
                    ${this.getRecommendation(troncon.prediction_ia.niveau, troncon.lineaire_ml)}
                </td>
            `;
            
            tableBody.appendChild(row);
        });
        
        section.style.display = 'block';
    }
    
    displayAIStats(data) {
        const section = document.getElementById('aiStatsSection');
        const content = document.getElementById('aiStatsContent');
        
        if (!data) {
            section.style.display = 'none';
            return;
        }
        
        const urgents = data.recommandations_globales?.troncons_urgents || [];
        const budget = data.recommandations_globales?.budget_estime || 0;
        
        const html = `
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-primary">${data.troncons_avec_predictions?.length || 0}</h3>
                        <p class="text-muted">Tronçons analysés</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="${urgents.length > 0 ? 'text-danger' : 'text-success'}">
                            ${urgents.length}
                        </h3>
                        <p class="text-muted">Tronçons urgents</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-info">${Math.round(budget / 1000)}K</h3>
                        <p class="text-muted">Budget estimé (FCFA)</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-warning">${this.calculatePriorityScore(data)}%</h3>
                        <p class="text-muted">Score de criticité</p>
                    </div>
                </div>
            </div>
        `;
        
        content.innerHTML = html;
        section.style.display = 'block';
    }
    
    getPriorityColor(priority) {
        const colors = {
            0: 'bg-success',
            1: 'bg-warning',
            2: 'bg-orange',
            3: 'bg-danger'
        };
        return colors[priority] || 'bg-secondary';
    }
    
    getRecommendation(priority, length) {
        const recommendations = {
            0: 'Maintenance programmée',
            1: 'Inspection dans 6 mois',
            2: 'Intervention dans 1 mois',
            3: 'Intervention immédiate'
        };
        return recommendations[priority] || 'À évaluer';
    }
    
    calculatePriorityScore(data) {
        if (!data || !data.troncons_avec_predictions) return 0;
        
        const totalPriority = data.troncons_avec_predictions.reduce((sum, t) => {
            return sum + (t.prediction_ia?.niveau || 0);
        }, 0);
        
        const avgPriority = totalPriority / data.troncons_avec_predictions.length;
        return Math.min(100, Math.round(avgPriority * 25));
    }
}

// ==================== APPLICATION PRINCIPALE ====================
class UrbanAIApp {
    constructor() {
        this.config = new UrbanAIConfig();
        this.dataManager = new DataManager(this.config);
        this.uiManager = new UIManager(this.config, this.dataManager);
        this.imageManager = new ImageManager(this.config);
        this.aiManager = new AIManager(this.config);
        
        this.init();
    }
    
    async init() {
        console.log('🏙️ Urban AI - Application initialisée');
        
        try {
            const villes = await this.dataManager.loadVilles();
            this.uiManager.populateVilleSelect(villes);
        } catch (error) {
            console.error('Erreur initialisation:', error);
            this.uiManager.showError('Erreur lors du chargement des villes');
        }
    }
    
    async displayIndicateurs(indicateurs) {
        // Afficher les images
        this.imageManager.displayTronconsGallery(indicateurs.troncons_voirie);
        this.imageManager.displayTaudisGallery(indicateurs.quartiers_taudis);
        
        // Mettre à jour l'interface
        this.uiManager.showNotification(`Données chargées pour ${indicateurs.commune}`, 'success');
    }
    
    async generateAIRecommendations() {
        const commune = this.config.currentCommune;
        
        if (!commune) {
            this.uiManager.showNotification('Veuillez sélectionner une commune', 'warning');
            return;
        }
        
        // Afficher le statut
        const statusElement = document.getElementById('aiStatusMessage');
        statusElement.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-cog fa-spin"></i> Génération des recommandations IA...
            </div>
        `;
        
        try {
            const aiData = await this.aiManager.getAIRecommendations(commune);
            
            // Afficher les recommandations
            this.aiManager.displayAIRecommendations(aiData);
            this.aiManager.updatePriorityScore(aiData);
            this.aiManager.displayAIPredictions(aiData);
            this.aiManager.displayAIStats(aiData);
            
            // Mettre à jour le statut
            statusElement.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> Recommandations IA générées avec succès
                </div>
            `;
            
            this.uiManager.showNotification('Analyse IA terminée', 'success');
            
        } catch (error) {
            console.error('Erreur recommandations IA:', error);
            
            statusElement.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i> Erreur: ${error.message}
                </div>
            `;
            
            this.uiManager.showNotification(`Erreur IA: ${error.message}`, 'error');
        }
    }
    
    toggleImageAnalysis() {
        this.config.imageAnalysisMode = !this.config.imageAnalysisMode;
        
        if (this.config.imageAnalysisMode) {
            this.uiManager.showNotification('Mode analyse IA activé', 'info');
        }
        
        // Recharger les images avec les boutons d'analyse
        if (this.config.currentData) {
            this.displayIndicateurs(this.config.currentData);
        }
    }
    
    async analyzeAllImages() {
        if (!this.config.currentData) {
            this.uiManager.showNotification('Aucune donnée disponible', 'warning');
            return;
        }
        
        this.uiManager.showNotification('Cette fonctionnalité est en développement', 'info');
    }
    
    openImageModal(imageUrl, title) {
        this.imageManager.openImageModal(imageUrl, title);
    }
    
    analyzeImage(imageUrl, title, imageType) {
        this.imageManager.analyzeImage(imageUrl, title, imageType);
    }
    
    checkAIStatus() {
        this.config.checkAIStatus();
    }
}

// ==================== INITIALISATION ====================
// Créer une instance globale accessible
window.urbanAI = new UrbanAIApp();

// Fonctions globales pour les événements onclick
window.getAIRecommendations = () => urbanAI.generateAIRecommendations();
window.enableImageAnalysis = () => urbanAI.toggleImageAnalysis();
window.analyzeAllImages = () => urbanAI.analyzeAllImages();
window.checkAIStatus = () => urbanAI.checkAIStatus();

// Initialiser quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 Urban AI - Interface chargée');
    
    // Initialiser les tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialiser les popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});