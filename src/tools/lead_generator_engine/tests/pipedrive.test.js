/**
 * Testes do PipedriveIntegration
 */

process.env.USE_MOCK = 'true';
process.env.PIPEDRIVE_API_TOKEN = 'test_token_placeholder';

const PipedriveIntegration = require('../pipedrive_integration');

describe('PipedriveIntegration', () => {

    describe('syncLeads() em modo mock', () => {
        it('deve retornar contagem correta de leads criados', async () => {
            const crm = new PipedriveIntegration();
            const leads = [
                { nome: 'Empresa A', telefone: 'N/A', email: 'N/A', site: 'N/A', endereco: 'RJ', rating: 5, origem: 'Maps' },
                { nome: 'Empresa B', telefone: 'N/A', email: 'N/A', site: 'N/A', endereco: 'SP', rating: 4, origem: 'Maps' },
                { nome: 'Empresa C', telefone: 'N/A', email: 'N/A', site: 'N/A', endereco: 'MG', rating: 3, origem: 'Apify' }
            ];
            const result = await crm.syncLeads(leads);
            expect(result.criados).toBe(3);
            expect(result.ignorados).toBe(0);
            expect(result.erros).toBe(0);
        });

        it('deve retornar zeros para lista vazia', async () => {
            const crm = new PipedriveIntegration();
            const result = await crm.syncLeads([]);
            expect(result.criados).toBe(0);
            expect(result.ignorados).toBe(0);
            expect(result.erros).toBe(0);
        });
    });

    describe('validação de ambiente', () => {
        it('deve lançar erro se PIPEDRIVE_API_TOKEN ausente e não for mock', () => {
            const originalMock = process.env.USE_MOCK;
            const originalToken = process.env.PIPEDRIVE_API_TOKEN;

            process.env.USE_MOCK = 'false';
            delete process.env.PIPEDRIVE_API_TOKEN;

            expect(() => new PipedriveIntegration()).toThrow('PIPEDRIVE_API_TOKEN');

            process.env.USE_MOCK = originalMock;
            process.env.PIPEDRIVE_API_TOKEN = originalToken;
        });
    });
});
