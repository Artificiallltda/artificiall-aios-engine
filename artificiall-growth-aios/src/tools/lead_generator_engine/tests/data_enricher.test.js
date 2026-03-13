/**
 * Testes do DataEnricher
 */

process.env.USE_MOCK = 'true';
process.env.GEMINI_API_KEY = 'test_key_placeholder';

const DataEnricher = require('../data_enricher');

describe('DataEnricher', () => {

    describe('cleanCompanyName() em modo mock', () => {
        it('deve remover sufixo LTDA do nome', async () => {
            const enricher = new DataEnricher();
            const result = await enricher.cleanCompanyName('Padaria Feliz LTDA');
            expect(result).not.toContain('LTDA');
        });

        it('deve remover sufixo ME do nome', async () => {
            const enricher = new DataEnricher();
            const result = await enricher.cleanCompanyName('Academia Forte ME');
            expect(result).not.toContain(' ME');
        });

        it('deve adicionar sufixo (Tratado) no modo mock', async () => {
            const enricher = new DataEnricher();
            const result = await enricher.cleanCompanyName('Empresa Qualquer');
            expect(result).toContain('(Tratado)');
        });
    });

    describe('findEmailsOnWebsite()', () => {
        it('deve retornar N/A se o site estiver inacessível', async () => {
            const enricher = new DataEnricher();
            const result = await enricher.findEmailsOnWebsite('http://site-inexistente-xyz123.com.br');
            expect(result).toBe('N/A');
        });
    });

    describe('enrichLeads() em modo mock', () => {
        it('deve processar todos os leads sem erros', async () => {
            const enricher = new DataEnricher();
            const leads = [
                { nome: 'Empresa A LTDA', site: 'N/A' },
                { nome: 'Empresa B ME', site: 'N/A' }
            ];
            const result = await enricher.enrichLeads(leads);
            expect(result).toHaveLength(2);
            result.forEach(lead => {
                expect(lead.email).toBe('N/A');
                expect(lead.nome_original).toBeDefined();
            });
        });
    });
});
