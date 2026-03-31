/**
 * Agente Enriquecedor de Dados (O Tratador)
 * Versão: 1.0.0
 * 
 * Melhora a qualidade dos dados brutos usando IA (Gemini) e técnicas de Scraping.
 */

require('dotenv').config();
const { GoogleGenerativeAI } = require('@google/generative-ai');
const axios = require('axios');

class DataEnricher {
    constructor() {
        this.useMock = process.env.USE_MOCK === 'true';
        this.apiKey = process.env.GEMINI_API_KEY;

        if (!this.apiKey && !this.useMock) {
            throw new Error('ERRO: A variável GEMINI_API_KEY não foi configurada no arquivo .env.');
        }

        if (!this.useMock) {
            const genAI = new GoogleGenerativeAI(this.apiKey);
            // gemini-1.5-flash nao existe — usar gemini-2.0-flash (modelo estavel atual)
            this.model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
        }
    }

    /**
     * Fluxo principal de enriquecimento para uma lista de leads.
     */
    async enrichLeads(leads) {
        console.log(`[ENRICHER] Enriquecendo ${leads.length} leads...`);

        for (let i = 0; i < leads.length; i++) {
            const lead = leads[i];
            console.log(`[ENRICHER] Processando lead ${i + 1}/${leads.length}: "${lead.nome}"`);

            // 1. Limpeza de Nome via IA (Gemini)
            lead.nome_original = lead.nome;
            lead.nome = await this.cleanCompanyName(lead.nome);

            // 2. Extração de E-mails do Site (Bônus)
            if (lead.site && lead.site !== 'N/A') {
                lead.email = await this.findEmailsOnWebsite(lead.site);
            } else {
                lead.email = 'N/A';
            }
        }

        return leads;
    }

    /**
     * Usa o Gemini para transformar nomes jurídicos em nomes fantasia amigáveis.
     */
    async cleanCompanyName(rawName) {
        if (this.useMock) {
            console.log(`[ENRICHER] 🧪 MODO MOCK: Simulando limpeza do nome "${rawName}"...`);
            return rawName.replace(' LTDA', '').replace(' ME', '') + ' (Tratado)';
        }

        try {
            const prompt = `Você é um assistente comercial. Limpe o nome da empresa abaixo para ser usado em um CRM de vendas. 
            Remova termos jurídicos como LTDA, ME, S.A., EPP, LTDA - ME. 
            Mantenha apenas o Nome Fantasia amigável e limpo.
            
            Entrada: "${rawName}"
            Saída (apenas o nome limpo):`;

            const result = await this.model.generateContent(prompt);
            const response = await result.response;
            return response.text().trim();
        } catch (error) {
            console.warn(`[ENRICHER] Falha ao limpar nome "${rawName}":`, error.message);
            return rawName; // Fallback para o nome original
        }
    }

    /**
     * Tenta capturar e-mails simples na página inicial do site.
     */
    async findEmailsOnWebsite(url) {
        try {
            console.log(`[ENRICHER] Buscando e-mail em: ${url}`);
            const response = await axios.get(url, { timeout: 8000 });
            const html = response.data;

            // Regex simples para capturar e-mails
            const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
            const matches = html.match(emailRegex);

            if (matches && matches.length > 0) {
                // Remove duplicados e e-mails comuns de imagem/lixo
                const uniqueEmails = [...new Set(matches)].filter(e => !e.endsWith('.png') && !e.endsWith('.jpg'));
                return uniqueEmails.length > 0 ? uniqueEmails[0] : 'N/A';
            }
        } catch (error) {
            // Ignora erros de acesso ao site (ex: site fora do ar)
            // console.warn(`[ENRICHER] Erro ao acessar site ${url}`);
        }
        return 'N/A';
    }
}

module.exports = DataEnricher;
