/**
 * Agente de Integração AIOS (Nativo Artificiall)
 * Versão: 1.0.0
 *
 * Substitui o antigo Pipedrive.
 * Envia os leads enriquecidos diretamente para o backend do AIOS Engine (Railway),
 * que por sua vez salva no Supabase para exibir no Dashboard Vercel.
 */

require('dotenv').config();
const axios = require('axios');

class AiosIntegration {
    constructor() {
        this.useMock = process.env.USE_MOCK === 'true';
        // A URL do AIOS Engine rodando no Railway
        this.aiosApiUrl = process.env.AIOS_API_URL || 'https://artificiall-aios-engine-production.up.railway.app';
        this.webhookEndpoint = `${this.aiosApiUrl}/webhook/leads`;

        this.http = axios.create({
            headers: {
                'Content-Type': 'application/json'
                // Aqui podemos adicionar um 'x-api-key' ou 'Authorization'
                // se o AIOS Engine exigir autenticação futura.
            },
            timeout: 15000
        });
    }

    /**
     * Envia um lote (batch) de leads para o AIOS Engine
     */
    async syncLeads(leads) {
        console.log(`[AIOS-INTEGRATION] Prepara para enviar ${leads.length} leads para a nuvem Artificiall...`);

        if (this.useMock) {
            console.log(`[AIOS-INTEGRATION] 🧪 MODO MOCK: Simulando envio de ${leads.length} leads para o AIOS...`);
            return { criados: leads.length, ignorados: 0, erros: 0 };
        }

        const validLeads = leads.filter(lead => lead.nome && typeof lead.nome === 'string' && lead.nome.trim() !== '');
        const ignorados = leads.length - validLeads.length;

        if (ignorados > 0) {
            console.warn(`[AIOS-INTEGRATION] ⚠️ ${ignorados} leads ignorados por estarem sem nome.`);
        }

        if (validLeads.length === 0) {
            return { criados: 0, ignorados, erros: 0 };
        }

        try {
            console.log(`[AIOS-INTEGRATION] 📡 Disparando POST para ${this.webhookEndpoint}`);
            const response = await this.http.post(this.webhookEndpoint, {
                leads: validLeads,
                source: 'gerador_local'
            });

            console.log(`[AIOS-INTEGRATION] ✅ AIOS Engine recebeu os leads (Status: ${response.status})`);
            
            // Assume que a API do AIOS retorne as contagens de sucesso, caso contrário usa o total de validados
            const criados = response.data?.criados || validLeads.length;
            const errosDoServidor = response.data?.erros || 0;

            return { 
                criados: criados, 
                ignorados: ignorados, 
                erros: errosDoServidor 
            };

        } catch (error) {
            const apiMsg = error.response?.data?.error || error.message;
            console.error(`[AIOS-INTEGRATION] ❌ Erro ao enviar leads para o AIOS: ${apiMsg}`);
            return { 
                criados: 0, 
                ignorados: ignorados, 
                erros: validLeads.length 
            };
        }
    }
}

module.exports = AiosIntegration;
