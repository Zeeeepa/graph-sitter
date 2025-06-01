# Migration Checklist

## Phase 1: Internal Updates (High Priority)
- [ ] Update src/contexten/__init__.py (2 references)
- [ ] Update src/contexten/cli/commands/serve/main.py (14 references)
- [ ] Update src/contexten/extensions/events/client.py (1 references)
- [ ] Update src/contexten/extensions/events/codegen_app.py (1 references)
- [ ] Update src/contexten/extensions/events/modal/base.py (6 references)

## Phase 2: Example Updates (Medium Priority)
- [ ] Update examples/examples/webhooks_README.md (4 references)
- [ ] Update examples/examples/linear_webhooks/webhooks.py (4 references)
- [ ] Update examples/examples/snapshot_event_handler/event_handlers.py (2 references)
- [ ] Update examples/examples/github_checks/app.py (1 references)
- [ ] Update examples/examples/pr_review_bot/app.py (1 references)
- [ ] Update examples/examples/github_webhooks/webhooks.py (4 references)
- [ ] Update examples/examples/codegen_app/app.py (1 references)
- [ ] Update examples/examples/unified_webhooks/webhooks.py (4 references)
- [ ] Update examples/examples/ticket-to-pr/app.py (1 references)

## Phase 3: Documentation Updates (Low Priority)
- [ ] Update docs/migration-strategy.md (26 references)
- [ ] Update docs/integration-architecture.md (2 references)
- [ ] Update docs/implementation-roadmap.md (13 references)

## Phase 4: External Notifications (Medium Priority)
- [ ] Notify about fix_imports_codemod.py (2 references)
- [ ] Notify about fix_documentation_imports.py (1 references)
- [ ] Notify about scripts/analyze_dependencies.py (9 references)
