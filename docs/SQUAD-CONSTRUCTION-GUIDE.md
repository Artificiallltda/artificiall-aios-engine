# Guia Prático: Construção de Squads

> Guia passo a passo para criar squads no AIOS.
> Complemento do [WORKFLOW-GUIDE.md](./WORKFLOW-GUIDE.md)

---

## O Que é uma Squad?

Uma **Squad** é um pacote modular de agentes IA que trabalham juntos para um domínio específico.

```
Squad = Agentes + Tasks + Workflows + Config + Templates + Tools
```

| Componente | O que faz | Exemplo |
|---|---|---|
| **Agents** | Personas especializadas | pm.md, dev.md, qa.md |
| **Tasks** | Fluxos executáveis | create-feature.md, review-code.md |
| **Workflows** | Orquestrações multi-step | main-workflow.yaml |
| **Config** | Padrões e regras | coding-standards.md, tech-stack.md |
| **Templates** | Geradores de documentos | report-template.md |
| **Tools** | Integrações customizadas | custom-tool.js |

---

## Estrutura de Diretórios

```
./squads/minha-squad/
├── squad.yaml              # ← Manifesto (OBRIGATÓRIO)
├── README.md               # Documentação
├── config/
│   ├── coding-standards.md # Padrões de código
│   ├── tech-stack.md       # Stack tecnológico
│   └── source-tree.md      # Estrutura do projeto
├── agents/                 # Definições de agentes
│   ├── pm.md
│   ├── dev.md
│   └── qa.md
├── tasks/                  # Tarefas executáveis
│   └── dev-implement.md
├── workflows/              # Orquestrações
│   └── main-workflow.yaml
├── checklists/             # Checklists de validação
├── templates/              # Templates de documentos
├── tools/                  # Ferramentas customizadas
├── scripts/                # Scripts utilitários
└── data/                   # Dados estáticos
```

---

## Passo a Passo: Criando uma Squad

### Passo 1 — Definir o Propósito

Antes de qualquer código, responda:

1. **Qual domínio?** (ex: jurídico, e-commerce, DevOps)
2. **Quais papéis são necessários?** (ex: PM, Dev, QA, UX)
3. **Quais tarefas a squad executa?** (ex: criar feature, fazer deploy)
4. **Qual stack tecnológico?** (ex: Python/FastAPI, Node/Express)

> [!TIP]
> Use o `*design-squad` para gerar um blueprint automático a partir de um PRD ou spec.

---

### Passo 2 — Criar o Manifesto (`squad.yaml`)

Este é o arquivo mais importante. Define tudo sobre a squad.

```yaml
# === CAMPOS OBRIGATÓRIOS ===
name: minha-squad                     # kebab-case, identificador único
version: 1.0.0                        # Versionamento semântico

# === METADADOS ===
description: Descrição do que a squad faz
author: Seu Nome <email@example.com>
license: MIT
slashPrefix: minha                    # Prefixo dos comandos (@minha)

# === COMPATIBILIDADE AIOS ===
aios:
  minVersion: "2.1.0"
  type: squad

# === COMPONENTES ===
components:
  agents:
    - pm.md
    - dev.md
    - qa.md
  tasks:
    - dev-implement.md
  workflows:
    - main-workflow.yaml
  checklists: []
  templates: []
  tools: []
  scripts: []

# === CONFIGURAÇÃO ===
config:
  extends: extend                     # extend | override | none
  coding-standards: config/coding-standards.md
  tech-stack: config/tech-stack.md
  source-tree: config/source-tree.md

# === DEPENDÊNCIAS ===
dependencies:
  node: []
  python: []
  squads: []                          # Ex: etl-squad@^2.0.0

# === TAGS (descoberta) ===
tags:
  - dominio
  - automacao
```

#### Modos de Config

| Modo | Comportamento |
|---|---|
| `extend` | Adiciona regras da squad às regras core do AIOS |
| `override` | Substitui regras core pelas da squad |
| `none` | Configuração standalone |

---

### Passo 3 — Criar Agentes

Cada agente é um arquivo `.md` em `agents/` com frontmatter YAML.

**Exemplo: `agents/dev.md`**

```markdown
---
agent:
  name: dev
  role: Desenvolvedor Senior
  slashPrefix: dev
  description: Desenvolvedor fullstack que implementa features seguindo padrões do projeto
  skills:
    - Implementação de código
    - Testes unitários
    - Debugging
  tools:
    - terminal
    - file-editor
---

# @dev — Desenvolvedor Senior (Dex)

## Personalidade
Desenvolvedor pragmático e eficiente. Prioriza qualidade, testes e código limpo.

## Responsabilidades
1. Implementar features conforme especificação
2. Escrever testes unitários
3. Fazer debugging de issues
4. Seguir coding-standards do projeto

## Comandos
| Comando | Descrição |
|---------|-----------|
| `*implement {feature}` | Implementar feature |
| `*fix {issue}` | Corrigir bug |
| `*test {module}` | Criar/rodar testes |

## Regras
- Sempre seguir `config/coding-standards.md`
- Nunca commitar sem testes passando
- Documentar decisões técnicas
```

> [!IMPORTANT]
> Cada agente **DEVE** ter:
> - Frontmatter YAML com `agent:` block
> - Nome em kebab-case
> - Role e description claros
> - Comandos documentados

---

### Passo 4 — Criar Tasks

Tasks seguem o formato **TASK-FORMAT-SPECIFICATION-V1** e são o **ponto de entrada principal** da squad.

**Exemplo: `tasks/dev-implement.md`**

```markdown
---
task: implement-feature
responsavel: dev
responsavel_type: agent
atomic_layer: execution
version: 1.0.0
tags: [implementação, código]
---

# Task: Implementar Feature

## Entrada
- **Especificação**: Descrição detalhada da feature
- **Arquivos afetados**: Lista de arquivos a modificar/criar
- **Critérios de aceite**: O que define "pronto"

## Saída
- Código implementado seguindo coding-standards
- Testes unitários passando
- Documentação atualizada (se aplicável)

## Passos
1. Ler especificação completa
2. Identificar arquivos afetados
3. Implementar mudanças incrementalmente
4. Escrever testes para cada módulo alterado
5. Rodar suite de testes
6. Verificar lint e formatação

## Checklist
- [ ] Código segue coding-standards
- [ ] Testes unitários passando
- [ ] Sem erros de lint
- [ ] Sem dependências desnecessárias
- [ ] Documentação atualizada
```

> [!WARNING]
> Campos **obrigatórios** em toda task:
> `task`, `responsavel`, `responsavel_type`, `atomic_layer`, `Entrada`, `Saída`, `Checklist`

---

### Passo 5 — Criar Config

#### `config/coding-standards.md`

```markdown
# Coding Standards

## Gerais
- Indentação: 2 espaços
- Charset: UTF-8
- Line ending: LF

## Naming
- Variáveis/funções: camelCase
- Classes: PascalCase
- Arquivos: kebab-case
- Constantes: UPPER_SNAKE_CASE

## Commits
- Formato: `tipo(escopo): descrição`
- Tipos: feat, fix, docs, refactor, test, chore
```

#### `config/tech-stack.md`

```markdown
# Tech Stack

| Camada | Tecnologia |
|--------|-----------|
| Runtime | Node.js 20+ |
| Framework | Express / FastAPI |
| Banco | PostgreSQL 16 |
| Cache | Redis 7 |
| CI/CD | GitHub Actions |
```

#### `config/source-tree.md`

```markdown
# Source Tree

Documentar a estrutura esperada do projeto aqui.
```

---

### Passo 6 — Criar Workflow (v2)

Workflows definem a orquestração entre agentes.

**Exemplo: `workflows/main-workflow.yaml`**

```yaml
name: main-workflow
description: Fluxo principal de desenvolvimento
version: 1.0.0

phases:
  - name: planning
    agent: pm
    tasks:
      - create-spec
    on_error: halt
    timeout: 30m

  - name: implementation
    agent: dev
    tasks:
      - implement-feature
    depends_on: planning
    on_error: retry
    timeout: 60m

  - name: review
    agent: qa
    tasks:
      - review-code
    depends_on: implementation
    on_error: halt
    timeout: 30m

error_handling:
  max_retries: 2
  notification: true
```

---

### Passo 7 — Validar

```bash
@squad-creator
*validate-squad minha-squad
```

#### Output Esperado

```
Validating squad: minha-squad
═══════════════════════════════

✅ Manifest: Valid
✅ Structure: Complete
✅ Tasks: 1/1 valid
✅ Agents: 3/3 valid
⚠️ Warnings:
   - README.md is minimal (consider expanding)

Summary: VALID (1 warning)
```

---

## Fluxo Visual Completo

```
DEFINIR ──▸ MANIFESTO ──▸ AGENTES ──▸ TASKS ──▸ CONFIG ──▸ WORKFLOW ──▸ VALIDAR
(propósito)  (squad.yaml)  (agents/)   (tasks/)  (config/)  (workflows/)  (*validate)
```

---

## Checklist de Criação

Antes de usar a squad, confirme:

- [ ] `squad.yaml` com todos os campos obrigatórios
- [ ] Todos os agentes listados existem em `agents/`
- [ ] Todas as tasks listadas existem em `tasks/`
- [ ] Tasks seguem TASK-FORMAT-SPECIFICATION-V1
- [ ] Config files criados (coding-standards, tech-stack, source-tree)
- [ ] `*validate-squad` passa sem erros
- [ ] README.md documentando uso da squad

---

## Exemplo Real: elite-dev-squad

A squad existente do projeto:

```yaml
# squads/elite-dev-squad/squad.yaml
name: elite-dev-squad
version: 1.0.0
description: Squad de elite para desenvolvimento fullstack, bots, clones e apps.
author: Synkra AIOS
slashPrefix: elite

components:
  agents:
    - pm.md        # Product Manager
    - architect.md # Arquiteto de Software
    - dev.md       # Desenvolvedor
    - ux.md        # Designer UX
    - qa.md        # Quality Assurance
```

---

## Comandos Rápidos

| Comando | O que faz |
|---------|-----------|
| `*create-squad {nome}` | Cria squad com estrutura completa |
| `*create-squad {nome} --template etl` | Cria a partir de template |
| `*design-squad --docs ./prd.md` | Gera blueprint a partir de docs |
| `*create-squad {nome} --from-design` | Cria a partir de blueprint |
| `*validate-squad {nome}` | Valida estrutura contra schema |
| `*validate-squad {nome} --strict` | Valida em modo estrito (CI/CD) |
| `*list-squads` | Lista squads locais |
| `*analyze-squad {nome}` | Analisa e sugere melhorias |
| `*extend-squad {nome}` | Adiciona componentes |
| `*migrate-to-v2` | Migra para formato v2 |

---

## Templates Disponíveis

| Template | Para quê | Componentes |
|----------|----------|-------------|
| `basic` | Squad simples | 1 agent, 1 task |
| `etl` | Processamento de dados | 2 agents, 3 tasks, scripts |
| `agent-only` | Apenas agentes | 2 agents, sem tasks |

---

## Distribuição

```
┌──────────────────────────────────────────────────┐
│              NÍVEIS DE DISTRIBUIÇÃO               │
├──────────────────────────────────────────────────┤
│  Nível 1: LOCAL     → ./squads/      (Privado)   │
│  Nível 2: PÚBLICO   → github.com     (Gratuito)  │
│  Nível 3: MARKETPLACE → api.synkra   (Premium)   │
└──────────────────────────────────────────────────┘
```

| Nível | Comando | Quando usar |
|-------|---------|-------------|
| Local | `*create-squad` | Projeto próprio |
| Público | `*publish-squad` | Comunidade open-source |
| Marketplace | `*sync-squad-synkra` | Monetização |

---

## Regras de Ouro

| # | Regra | Motivo |
|---|---|---|
| 1 | Sempre validar antes de usar | Evita erros runtime |
| 2 | Task-first architecture | Tasks são o ponto de entrada |
| 3 | kebab-case em tudo | Padrão do AIOS |
| 4 | Uma squad por domínio | Separação de responsabilidades |
| 5 | Documentar o README | Outros devem entender a squad |
| 6 | Versionamento semântico | Compatibilidade garantida |

---

*Referência completa: [squads-guide.md](../aios-core/docs/guides/squads-guide.md) | [squad-creator-system.md](../aios-core/docs/aios-agent-flows/squad-creator-system.md)*
