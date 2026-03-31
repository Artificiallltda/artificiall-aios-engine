/**
 * Agente Coordenador (Maestro) - Gerador de Leads
 * Versão: 2.0.0
 *
 * Centraliza o controle das operações de extração, enriquecimento e integração.
 * Suporta múltiplas origens: maps, linkedin, apify.
 */

const MapsScraper = require('./maps_scraper');
const LinkedInScraper = require('./linkedin_scraper');
const ApifyScraper = require('./apify_scraper');
const DataEnricher = require('./data_enricher');
const AiosIntegration = require('./aios_integration');

function log(emoji, modulo, msg) {
    const ts = new Date().toISOString().replace('T', ' ').substring(0, 19);
    console.log(`[${ts}] ${emoji} [${modulo}] ${msg}`);
}

async function main() {
    const termoBusca = process.argv[2];
    const fonte = (process.argv[3] || 'maps').toLowerCase();

    if (!termoBusca) {
        log('❌', 'MAESTRO', 'Uso: node src/index.js "Termo de Busca" [maps|linkedin|apify]');
        process.exit(1);
    }

    log('🚀', 'MAESTRO', `Iniciando operação. Fonte: ${fonte.toUpperCase()} | Busca: "${termoBusca}"`);

    try {
        let rawLeads = [];

        // ── PASSO 1: Extração ────────────────────────────────────────────────
        log('🔍', 'MAESTRO', 'Passo 1/3 — Extraindo leads...');
        if (fonte === 'linkedin') {
            const scraper = new LinkedInScraper();
            rawLeads = await scraper.searchPeople(termoBusca);
        } else if (fonte === 'apify') {
            const scraper = new ApifyScraper();
            rawLeads = await scraper.searchPlaces(termoBusca);
        } else {
            const scraper = new MapsScraper();
            rawLeads = await scraper.searchPlaces(termoBusca);
        }

        if (rawLeads.length === 0) {
            log('⚠️', 'MAESTRO', 'Nenhum lead encontrado para este termo. Encerrando.');
            process.exit(0);
        }
        log('✅', 'MAESTRO', `${rawLeads.length} leads extraídos.`);

        // ── PASSO 2: Enriquecimento ──────────────────────────────────────────
        log('🧠', 'MAESTRO', 'Passo 2/3 — Enriquecendo dados com IA...');
        const enricher = new DataEnricher();
        const enrichedLeads = await enricher.enrichLeads(rawLeads);
        log('✅', 'MAESTRO', `${enrichedLeads.length} leads enriquecidos.`);

        // ── PASSO 3: AIOS INTEGRATION ────────────────────────────────────────
        log('📤', 'MAESTRO', 'Passo 3/3 — Enviando para a nuvem Artificiall (AIOS)...');
        const aios = new AiosIntegration();
        const resAios = await aios.syncLeads(enrichedLeads);
        log('✅', 'MAESTRO', `Leads enviados para o AIOS Engine.`);

        // ── RESUMO FINAL ─────────────────────────────────────────────────────
        const summary = {
            fonte: fonte.toUpperCase(),
            termo: termoBusca,
            extraidos: rawLeads.length,
            enriquecidos: enrichedLeads.length,
            crm_criados: resAios.criados,
            crm_ignorados: resAios.ignorados,
            crm_erros: resAios.erros,
            leads: enrichedLeads
        };

        console.log('\n=============================================');
        console.log(`RESUMO DA OPERAÇÃO (${fonte.toUpperCase()}):`);
        console.log(`- Leads extraídos      : ${summary.extraidos}`);
        console.log(`- Leads enriquecidos   : ${summary.enriquecidos}`);
        console.log(`- AIOS Supabase — OK   : ${summary.crm_criados}`);
        console.log(`- AIOS Supabase — Skip : ${summary.crm_ignorados}`);
        console.log(`- AIOS Supabase — Error: ${summary.crm_erros}`);
        console.log('=============================================');
        // JSON estruturado para o app.py capturar
        console.log('__SUMMARY_JSON__' + JSON.stringify(summary));

    } catch (error) {
        log('💥', 'MAESTRO', `Falha crítica: ${error.message}`);
        if (process.env.NODE_ENV !== 'production') {
            console.error(error.stack);
        }
        process.exit(1);
    }
}

main();
