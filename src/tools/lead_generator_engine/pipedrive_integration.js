/**
 * Agente de Integração CRM (O Vendedor Interno)
 * Versão: 3.0.0
 *
 * Fluxo correto da API do Pipedrive:
 *   1. Organização  → nome, endereço
 *   2. Person       → nome de contato, telefone, email (vinculado à Organização)
 *   3. Deal         → negócio vinculado à Organização + Person
 *   4. Nota         → site, rating e origem do lead
 *
 * SEGURANÇA: O api_token é enviado via header (x-api-token) e nunca fica exposto na URL.
 */

require('dotenv').config();
const axios = require('axios');

class PipedriveIntegration {
    constructor() {
        this.useMock = process.env.USE_MOCK === 'true';
        this.apiToken = process.env.PIPEDRIVE_API_TOKEN;
        this.baseUrl = 'https://api.pipedrive.com/v1';

        if (!this.apiToken && !this.useMock) {
            throw new Error('ERRO: A variável de ambiente PIPEDRIVE_API_TOKEN não foi configurada no arquivo .env.');
        }

        // Instância axios com header de autenticação seguro (não expõe token na URL)
        this.http = axios.create({
            baseURL: this.baseUrl,
            headers: {
                'Content-Type': 'application/json',
                'x-api-token': this.apiToken || ''
            },
            timeout: 15000
        });
    }

    /**
     * Fluxo principal: Processa uma lista de leads para o Pipedrive.
     */
    async syncLeads(leads) {
        console.log(`[PIPEDRIVE] Iniciando sincronização de ${leads.length} leads...`);

        if (this.useMock) {
            console.log(`[PIPEDRIVE] 🧪 MODO MOCK: Simulando criação de ${leads.length} deals no CRM...`);
            return { criados: leads.length, ignorados: 0, erros: 0 };
        }

        const results = { criados: 0, ignorados: 0, erros: 0 };

        for (const lead of leads) {
            // Validacao: pula leads sem nome (Pipedrive rejeita com 400)
            if (!lead.nome || typeof lead.nome !== 'string' || lead.nome.trim() === '') {
                console.warn(`[PIPEDRIVE] ⚠️  Lead ignorado por falta de nome:`, JSON.stringify(lead));
                results.ignorados++;
                continue;
            }

            lead.nome = lead.nome.trim();

            try {
                // 1. Verificar se a Organização já existe
                let orgId = await this.findOrganization(lead.nome);

                if (!orgId) {
                    // 2. Criar Organização (nome + endereço apenas)
                    orgId = await this.createOrganization(lead);
                    console.log(`[PIPEDRIVE] ✅ Organização criada: ${lead.nome} (ID: ${orgId})`);
                    results.criados++;
                } else {
                    console.log(`[PIPEDRIVE] ⏭️  Já existe: ${lead.nome} (ID: ${orgId}). Ignorando.`);
                    results.ignorados++;
                }

                // 3. Criar Person (contato) com telefone e email nativos, vinculado à Organização
                const personId = await this.createPerson(orgId, lead);
                if (personId) {
                    console.log(`[PIPEDRIVE] 👤 Contato criado: ${lead.nome} (Person ID: ${personId})`);
                }

                // 4. Criar Negócio (Deal) vinculado à Organização + Person
                await this.createDeal(orgId, personId, lead);

            } catch (error) {
                const apiMsg = error.response?.data?.error || error.message;
                console.error(`[PIPEDRIVE] ❌ Erro ao processar "${lead.nome}": ${apiMsg}`);
                if (error.response?.status === 400) {
                    console.error(`[PIPEDRIVE] Payload rejeitado:`, JSON.stringify(error.response?.data));
                }
                results.erros++;
            }
        }

        return results;
    }

    /**
     * Busca uma organização pelo nome exato para evitar duplicatas.
     */
    async findOrganization(name) {
        try {
            const response = await this.http.get('/organizations/search', {
                params: { term: name, fields: 'name', exact_match: true }
            });

            const items = response.data?.data?.items || [];
            return items.length > 0 ? items[0].item.id : null;
        } catch (error) {
            console.error('[PIPEDRIVE] Erro na busca de organização:', error.message);
            return null;
        }
    }

    /**
     * Cria uma nova organização no Pipedrive.
     * NOTA: Organizações NÃO aceitam phone/email — esses campos ficam na Person.
     */
    async createOrganization(lead) {
        const body = {
            name: lead.nome,
            address: lead.endereco || undefined
        };

        const response = await this.http.post('/organizations', body);
        return response.data.data.id;
    }

    /**
     * Cria uma Person (Contato) vinculada à Organização.
     * É aqui que telefone e e-mail são armazenados como campos nativos do Pipedrive.
     */
    async createPerson(orgId, lead) {
        try {
            const body = {
                name: lead.nome,
                org_id: orgId
            };

            // Telefone como campo nativo da Person (formato exigido pela API)
            if (lead.telefone && lead.telefone !== 'N/A') {
                body.phone = [{ value: lead.telefone, primary: true, label: 'work' }];
            }

            // E-mail como campo nativo da Person
            if (lead.email && lead.email !== 'N/A') {
                body.email = [{ value: lead.email, primary: true, label: 'work' }];
            }

            const response = await this.http.post('/persons', body);
            return response.data?.data?.id || null;
        } catch (error) {
            console.error('[PIPEDRIVE] ⚠️  Erro ao criar contato (Person):', error.response?.data?.error || error.message);
            return null; // Não bloqueia a criação do Deal
        }
    }

    /**
     * Cria um negócio (Deal) vinculado à Organização e à Person.
     */
    async createDeal(orgId, personId, lead) {
        try {
            const origem = lead.origem || 'MAPS';
            const dealPayload = {
                title: `[${origem}] ${lead.nome}`,
                org_id: orgId,
                status: 'open'
            };

            // Vincula o Deal ao contato (Person) se existir
            if (personId) {
                dealPayload.person_id = personId;
            }

            const dealRes = await this.http.post('/deals', dealPayload);
            const dealId = dealRes.data?.data?.id;

            // Cria uma nota com informações complementares do lead
            if (dealId) {
                await this.http.post('/notes', {
                    content: `<b>Site:</b> ${lead.site || 'N/A'}<br><b>Rating Google:</b> ${lead.rating || 'N/A'}<br><b>Origem:</b> ${lead.origem || 'N/A'}`,
                    deal_id: dealId
                });
            }
        } catch (error) {
            console.error('[PIPEDRIVE] ❌ Erro ao criar Negócio/Nota:', error.message);
        }
    }
}

module.exports = PipedriveIntegration;
