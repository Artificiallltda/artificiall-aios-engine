/**
 * Agente Scraper Maps (O Pesquisador Local)
 * Versão: 1.0.0
 * 
 * Este script é responsável por buscar empresas locais via Google Places API (v1).
 * 
 * Dependências necessárias:
 * npm install axios dotenv
 */

require('dotenv').config();
const axios = require('axios');

/**
 * Classe responsável pela extração de dados do Google Maps.
 */
class MapsScraper {
    constructor() {
        this.apiKey = process.env.GOOGLE_PLACES_API_KEY;
        this.apiUrl = 'https://places.googleapis.com/v1/places:searchText';
        this.useMock = process.env.USE_MOCK === 'true';

        if (!this.apiKey && !this.useMock) {
            throw new Error('ERRO: A variável de ambiente GOOGLE_PLACES_API_KEY não foi configurada no arquivo .env.');
        }
    }

    /**
     * Realiza a busca de estabelecimentos por termo.
     * @param {string} textQuery O termo de busca (Ex: "Clínicas de Estética em São Paulo").
     * @returns {Promise<Array>} Lista de leads formatados.
     */
    async searchPlaces(textQuery) {
        console.log(`[MAPS-SCRAPER] Iniciando busca por: "${textQuery}"...`);

        if (this.useMock) {
            console.log(`[MAPS-SCRAPER] 🧪 MODO MOCK: Retornando padarias de mentirinha para testes...`);
            return [
                { id_google: 'mock_1', nome: `Empresa Teste 1 - ${textQuery}`, endereco: "Rua das Simulações, 100", rating: 4.9, site: "https://site-teste-1.com.br", telefone: "+5511999999999", origem: 'Google Maps' },
                { id_google: 'mock_2', nome: `Super Empresa 2 (Mock)`, endereco: "Av. dos Testes, 200", rating: 4.5, site: "https://site-teste-2.com.br", telefone: "+5511888888888", origem: 'Google Maps' }
            ];
        }

        try {
            const response = await axios.post(
                this.apiUrl,
                { textQuery },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Goog-Api-Key': this.apiKey,
                        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.rating,places.websiteUri,places.internationalPhoneNumber,places.id'
                    },
                    timeout: 10000
                }
            );

            const places = response.data.places || [];
            console.log(`[MAPS-SCRAPER] Foram encontrados ${places.length} estabelecimentos.`);

            return this.formatLeads(places);
        } catch (error) {
            console.error('[MAPS-SCRAPER] Falha na requisição:', error.response ? error.response.data : error.message);
            throw new Error('Erro ao buscar dados no Google Places API.');
        }
    }

    /**
     * Formata os dados brutos da API em um JSON limpo para o sistema.
     * @param {Array} rawPlaces Dados brutos recebidos da API.
     * @returns {Array} Leads formatados.
     */
    formatLeads(rawPlaces) {
        return rawPlaces.map(place => ({
            id_google: place.id,
            nome: place.displayName?.text || 'N/A',
            endereco: place.formattedAddress || 'N/A',
            telefone: place.internationalPhoneNumber || 'N/A',
            site: place.websiteUri || 'N/A',
            rating: place.rating || 0,
            origem: 'Google Maps'
        }));
    }
}

// Exporta para ser usado pelo Agente Coordenador ou outros módulos
module.exports = MapsScraper;

/**
 * Script de Teste (Execução direta via node src/maps_scraper.js)
 */
if (require.main === module) {
    (async () => {
        const scraper = new MapsScraper();
        try {
            const termoBusca = process.argv[2] || "Clínicas de Estética em São Paulo";
            const leads = await scraper.searchPlaces(termoBusca);

            console.log(`\n--- Resultado da Extração(Primeiros 3 Leads) ---`);
            console.log(JSON.stringify(leads.slice(0, 3), null, 2));

            // Aqui poderíamos salvar em arquivo no futuro se necessário
        } catch (err) {
            console.error('[MAIN] Erro:', err.message);
        }
    })();
}
