.PHONY: test
test:
	uv run pytest

.PHONY: test-fast
test-fast:
	uv run pytest tests/test_summary.py tests/test_adb.py tests/test_files.py

.PHONY: test-cli
test-cli:
	uv run pytest tests/test_cli.py tests/test_processes.py

.PHONY: sync
sync:
	uv sync --extra dev --extra tracing --extra hf

.PHONY: setup
setup:
	uv run python scripts/setup.py

.PHONY: app-audit
app-audit:
	uv run python scripts/tools/app_audit.py

.PHONY: smoke-test
smoke-test:
	./scripts/run/smoke_test.sh

.PHONY: organize-public
organize-public:
	uv run python scripts/tools/organize_public_artifacts.py --sweep

.PHONY: help
help:
	@printf "Targets:\n"
	@printf "  make sync        Create/update the uv-managed .venv with all extras\n"
	@printf "  make setup       One-command onboarding: prereqs, deps, env/config, device, manifests, day-vars\n"
	@printf "  make app-audit   Check the connected phone has the 22 benchmark apps\n"
	@printf "  make test        Run the full pytest suite\n"
	@printf "  make test-fast   Run fast parser/helper coverage\n"
	@printf "  make test-cli    Run harness CLI/process coverage\n"
	@printf "  make smoke-test  Pre-flight check: LLM server, wired/wireless ADB + mobilerun, one real task\n"
	@printf "  make organize-public  File all public-run artifacts into per-run folders + rebuild turn-based audits\n"
