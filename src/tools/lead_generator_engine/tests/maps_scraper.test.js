/**
 * Testes do MapsScraper
 */

// Força modo mock para todos os testes
process.env.USE_MOCK = 'true';
process.env.GOOGLE_PLACES_API_KEY = 'test_key_placeholder';

const MapsScraper = require('../maps_scraper');

describe('MapsScraper', () => {

    describe('formatLeads()', () => {
        it('deve formatar corretamente os dados brutos da API', () => {
            const scraper = new MapsScraper();
            const rawData = [{
                id: 'place_001',
                displayName: { text: 'Padaria Feliz LTDA' },
                formattedAddress: 'Rua das Flores, 100',
                internationalPhoneNumber: '+5541999991111',
                websiteUri: 'https://padariafeliz.com.br',
                rating: 4.7
            }];

            const leads = scraper.formatLeads(rawData);
            expect(leads).toHaveLength(1);
            expect(leads[0]).toMatchObject({
                id_google: 'place_001',
                nome: 'Padaria Feliz LTDA',
                endereco: 'Rua das Flores, 100',
                telefone: '+5541999991111',
                site: 'https://padariafeliz.com.br',
                rating: 4.7,
                origem: 'Google Maps'
            });
        });

        it('deve preencher N/A para campos ausentes', () => {
            const scraper = new MapsScraper();
            const leads = scraper.formatLeads([{ id: 'x', displayName: {} }]);
            expect(leads[0].nome).toBe('N/A');
            expect(leads[0].endereco).toBe('N/A');
            expect(leads[0].telefone).toBe('N/A');
            expect(leads[0].site).toBe('N/A');
            expect(leads[0].rating).toBe(0);
        });
    });

    describe('searchPlaces() em modo mock', () => {
        it('deve retornar 2 leads simulados', async () => {
            const scraper = new MapsScraper();
            const leads = await scraper.searchPlaces('Padarias em Curitiba');
            expect(leads).toHaveLength(2);
            expect(leads[0].origem).toBe('Google Maps');
            expect(leads[0].nome).toContain('Padarias em Curitiba');
        });
    });

    describe('validação de ambiente', () => {
        it('deve lançar erro se API key ausente e não for mock', () => {
            const originalMock = process.env.USE_MOCK;
            const originalKey = process.env.GOOGLE_PLACES_API_KEY;

            process.env.USE_MOCK = 'false';
            delete process.env.GOOGLE_PLACES_API_KEY;

            expect(() => new MapsScraper()).toThrow('GOOGLE_PLACES_API_KEY');

            process.env.USE_MOCK = originalMock;
            process.env.GOOGLE_PLACES_API_KEY = originalKey;
        });
    });
});
