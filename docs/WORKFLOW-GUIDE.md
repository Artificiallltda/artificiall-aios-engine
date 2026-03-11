# Workflow: Antigravity + AIOS

Guia prático para construção de projetos usando os dois assistentes em conjunto.

---

## Fases do Desenvolvimento

### Fase 1 — Planejamento (Antigravity)

> Antes de escrever qualquer código.

1. Descreva o projeto para o Antigravity
2. Antigravity cria: **PRD**, **STRUCTURE-GUIDE**, arquitetura
3. Antigravity escreve os **arquivos-âncora** (entry point, router, engine principal)
4. Antigravity gera a **lista de sprints** com instruções para o AIOS

### Fase 2 — Geração (AIOS)

> Criar código novo seguindo o plano.

5. Cole as instruções da sprint no AIOS
6. **Sempre inclua:** `"NÃO modifique [lista de arquivos protegidos]"`
7. Uma sprint por vez, nunca tudo junto

### Fase 3 — Revisão (Antigravity)

> Antes de continuar para a próxima sprint.

8. Antigravity faz code review com issues numerados
9. Cole os issues para o AIOS corrigir
10. Antigravity verifica se corrigiu sem quebrar

### Fase 4 — Deploy (Antigravity)

> Git, testes, deploy.

11. Antigravity faz git (commit, push, restore)
12. Antigravity debuga falhas no deploy
13. Próxima sprint → volta para Fase 2

---

## Fluxo Visual

```
PLANEJAR ──▸ GERAR ──▸ REVISAR ──▸ DEPLOY ──▸ próxima sprint
(Antigravity)  (AIOS)  (Antigravity) (Antigravity)
```

---

## Regras de Ouro

| # | Regra | Motivo |
|---|---|---|
| 1 | AIOS nunca toca em arquivos-âncora | Ele reescreve inteiro e quebra a arquitetura |
| 2 | Uma sprint por vez | Múltiplas sprints = mais bugs acumulados |
| 3 | Sempre revisar antes de avançar | AIOS gera bugs sutis (escapes, imports, types) |
| 4 | Git commit antes de mandar o AIOS alterar | Para poder reverter com `git checkout` |
| 5 | Seed scripts e templates: Antigravity faz | AIOS simplifica demais e perde funcionalidade |
| 6 | Sempre dizer "NÃO modifique X" | AIOS sobrescreve arquivos que não pediu pra alterar |

---

## Quem Faz o Quê

| Tarefa | Antigravity | AIOS |
|---|---|---|
| PRD e arquitetura | ✅ | |
| Criar muitos arquivos novos | | ✅ |
| Code review | ✅ | |
| Editar sem quebrar | ✅ | |
| Git (commit, push, rollback) | ✅ | |
| Conteúdo (KB, templates, seeds) | ✅ | |
| Debugging e root cause | ✅ | |
| Gerar sprints rápido | | ✅ |

---

## Checklist Pré-Sprint (para o AIOS)

Antes de enviar instruções ao AIOS, confirme:

- [ ] Git commitado (para poder reverter)
- [ ] Lista de arquivos protegidos definida
- [ ] Instruções claras e específicas
- [ ] Apenas 1 sprint por vez
- [ ] Code review da sprint anterior aprovado
