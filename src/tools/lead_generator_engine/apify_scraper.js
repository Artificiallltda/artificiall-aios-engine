/**
 * Agente Scraper Apify (Motor Profissional de Leads)
 * Versão: 1.0.0
 *
 * Usa a plataforma Apify para extrair leads de forma robusta e escalável,
 * utilizando o ator "compass/crawler-google-places" via API REST.
 *
 * Requer: APIFY_TOKEN no arquivo .env
 */

require('dotenv').config();
const axios = require('axios');

class ApifyScraper {
    constructor() {
        this.apiToken = process.env.APIFY_TOKEN;
        this.useMock = process.env.USE_MOCK === 'true';
        this.actorId = 'compass~crawler-google-places';
        this.baseUrl = 'https://api.apify.com/v2';

        if (!this.apiToken && !this.useMock) {
            throw new Error('ERRO: A variável de ambiente APIFY_TOKEN não foi configurada no arquivo .env.');
        }
    }

    /**
     * Busca estabelecimentos via Apify Google Places Actor.
     * @param {string} textQuery Termo de busca.
     * @returns {Promise<Array>} Lista de leads formatados.
     */
    async searchPlaces(textQuery) {
        console.log(`[APIFY-SCRAPER] Iniciando busca por: "${textQuery}"...`);

        if (this.useMock) {
            console.log('[APIFY-SCRAPER] 🧪 MODO MOCK: Retornando leads simulados do Apify...');
            return [
                { id_google: 'apify_mock_1', nome: `[Apify] Empresa Alpha - ${textQuery}`, endereco: 'Rua Apify, 100, São Paulo', telefone: '+5511911111111', site: 'https://alpha.com.br', rating: 4.8, origem: 'Apify' },
                { id_google: 'apify_mock_2', nome: '[Apify] Empresa Beta (Mock)', endereco: 'Av. Robusta, 500, Rio de Janeiro', telefone: '+5521922222222', site: 'https://beta.com.br', rating: 4.6, origem: 'Apify' }
            ];
        }

        try {
            // 1. Dispara o ator
            console.log('[APIFY-SCRAPER] Disparando ator no Apify...');
            const runRes = await axios.post(
                `${this.baseUrl}/acts/${this.actorId}/runs?waitForFinish=120`,
                {
                    searchStringsArray: [textQuery],
                    maxCrawledPlacesPerSearch: 60,
                    language: 'pt-BR',
                    countryCode: 'br'
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.apiToken}`
                    },
                    timeout: 150000
                }
            );

            const datasetId = runRes.data.data.defaultDatasetId;
            console.log(`[APIFY-SCRAPER] Ator finalizado. Dataset ID: ${datasetId}`);

            // 2. Busca os resultados do dataset
            const dataRes = await axios.get(
                `${this.baseUrl}/datasets/${datasetId}/items?clean=true&format=json`,
                { headers: { 'Authorization': `Bearer ${this.apiToken}` } }
            );

            const items = dataRes.data || [];
            console.log(`[APIFY-SCRAPER] ${items.length} estabelecimentos encontrados.`);
            return this.formatLeads(items);

        } catch (error) {
            const msg = error.response ? JSON.stringify(error.response.data) : error.message;
            console.error('[APIFY-SCRAPER] Falha na chamada à API:', msg);
            throw new Error('Erro ao buscar dados via Apify.');
        }
    }

    /**
     * Formata os dados brutos do Apify para o formato padrão do sistema.
     */
    formatLeads(rawItems) {
        return rawItems.map(item => ({
            id_google: item.placeId || item.cid || 'N/A',
            nome: item.title || 'N/A',
            endereco: item.address || 'N/A',
            telefone: item.phone || 'N/A',
            site: item.website || 'N/A',
            rating: item.totalScore || 0,
            origem: 'Apify'
        }));
    }
}

module.exports = ApifyScraper;
