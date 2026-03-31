const fs = require('fs');
const path = require('path');

// Reutilizar lógica do framework
const parser = require('./.aiox-core/infrastructure/scripts/ide-sync/agent-parser');
const transformer = require('./.aiox-core/infrastructure/scripts/ide-sync/transformers/claude-code');

const syncSquad = (squadName, squadPath) => {
  console.log(`\n🔄 Sincronizando Squad: ${squadName}`);
  const agentsDir = path.join(squadPath, 'agents');
  
  if (!fs.existsSync(agentsDir)) {
    console.log(`⚠️  Pasta de agentes não encontrada: ${agentsDir}`);
    return;
  }

  const agents = parser.parseAllAgents(agentsDir);
  console.log(`   Encontrados ${agents.length} agentes no squad.`);

  // Destinos (Claude e Gemini)
  const TARGET_IDES = [
  { name: 'claude', path: '.claude/commands', format: 'md' },
  { name: 'gemini', path: '.gemini/rules', format: 'md' },
  { name: 'qwen', path: '.qwen/commands', format: 'md' }
];

  for (const target of TARGET_IDES) {
    const targetDir = path.resolve(target.path, squadName, 'agents');
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
    
    for (const agent of agents) {
      if (agent.error && agent.error !== 'YAML parse failed, using fallback extraction') {
         console.log(`   ❌ Erro no agente ${agent.id}: ${agent.error}`);
         continue;
      }
      
      try {
        const content = transformer.transform(agent);
        const filename = transformer.getFilename(agent);
        fs.writeFileSync(path.join(targetDir, filename), content);
      } catch (e) {
        console.log(`   ❌ Erro ao transformar/gravar ${agent.id}: ${e.message}`);
      }
    }
    console.log(`   ✅ Sincronizado com ${target.name} em ${target.path}`);
  }
};

// Executar para os squads detectados
const squadsRoot = 'squads';
if (fs.existsSync(squadsRoot)) {
  const squads = fs.readdirSync(squadsRoot, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);

  for (const squad of squads) {
    syncSquad(squad, path.join(squadsRoot, squad));
  }
}
