/**
 * Agente Scraper LinkedIn (O Headhunter)
 * Versão: 1.0.0
 * 
 * Especialista em navegação web e simulação de perfil humano para extração corporativa.
 */

require('dotenv').config();
const { chromium } = require('playwright');

class LinkedInScraper {
    constructor() {
        this.useMock = process.env.USE_MOCK === 'true';
        this.email = process.env.LINKEDIN_EMAIL;
        this.password = process.env.LINKEDIN_PASSWORD;
    }

    /**
     * Inicia a extração de perfis do LinkedIn.
     * @param {string} query Termo de busca (Ex: "CEO de Clínicas em São Paulo").
     * @returns {Promise<Array>} Lista de leads extraídos.
     */
    async searchPeople(query) {
        console.log(`[LINKEDIN-SCRAPER] Iniciando busca por: "${query}"...`);

        if (this.useMock) {
            console.log(`[LINKEDIN-SCRAPER] 🧪 MODO MOCK: Simulando extração de executivos no LinkedIn...`);
            return [
                { nome: `João Diretor - ${query}`, cargo: 'Investidor e CEO', endereco: 'São Paulo', site: 'https://linkedin.com/in/joaomock', origem: 'LinkedIn', telefone: 'N/A' },
                { nome: `Maria Executiva (Mock)`, cargo: 'Head de Operações', endereco: 'Rio de Janeiro', site: 'https://linkedin.com/in/mariamock', origem: 'LinkedIn', telefone: 'N/A' }
            ];
        }

        const browser = await chromium.launch({ headless: false }); // Headless: false para testes iniciais
        const context = await browser.newContext();
        const page = await context.newPage();

        try {
            // 1. Login no LinkedIn
            await page.goto('https://www.linkedin.com/login');
            await page.fill('#username', this.email);
            await page.fill('#password', this.password);
            await page.click('[type="submit"]');

            // Aguarda o dashboard carregar
            await page.waitForURL('https://www.linkedin.com/feed/');
            console.log('[LINKEDIN-SCRAPER] Login realizado com sucesso.');

            // 2. Realiza a busca
            const searchUrl = `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(query)}`;
            await page.goto(searchUrl);
            await page.waitForTimeout(5000); // Aguarda carregamento humano

            // 3. Extrai dados dos resultados (Mock inicial/Simulado)
            // Nota: Em produção, o script navegaria por cada resultado para extrair detalhes
            const leads = await page.evaluate(() => {
                const results = [];
                const cards = document.querySelectorAll('.reusable-search__result-container');

                cards.forEach(card => {
                    const name = card.querySelector('.entity-result__title-text a')?.innerText.split('\\n')[0];
                    const job = card.querySelector('.entity-result__primary-subtitle')?.innerText;
                    const location = card.querySelector('.entity-result__secondary-subtitle')?.innerText;
                    const profileLink = card.querySelector('.entity-result__title-text a')?.href;

                    if (name) {
                        results.push({
                            nome: name,
                            cargo: job,
                            endereco: location,
                            site: profileLink, // Link do perfil
                            origem: 'LinkedIn'
                        });
                    }
                });
                return results;
            });

            console.log(`[LINKEDIN-SCRAPER] Encontrados ${leads.length} profissionais.`);
            return leads;

        } catch (error) {
            console.error('[LINKEDIN-SCRAPER] Erro fatal:', error.message);
            throw error;
        } finally {
            await browser.close();
        }
    }
}

module.exports = LinkedInScraper;
