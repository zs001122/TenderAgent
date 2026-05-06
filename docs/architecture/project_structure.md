# Project Structure

> Last updated: 2026-05-06

This repository is organized around four active surfaces: backend API, frontend UI, crawler ingestion, and project operations.

## Active Directories

- `backend/`: FastAPI service, SQLModel models, migrations, backend scripts, and backend tests.
- `frontend/`: React/Vite application, frontend services, pages, components, and build configuration.
- `crawlers/`: Independent crawler subsystem. It remains outside `backend/`; backend pipeline scripts call it when ingestion is needed.
- `scripts/`: Project-level operational scripts, including cross-platform MVP startup and utility scripts.
- `docs/`: Current architecture notes, implementation plans, and development logs.
- `deploy/`: Deployment notes and deployment-related configuration.

## Documentation Directories

- `docs/architecture/`: Current architecture and structure references.
- `docs/plans/`: Active module plans.
- `docs/dev-logs/`: Development logs by module.
- `docs/archive/`: Old plans and historical notes kept for reference only.
- `.trae/documents/`: Execution-board documents kept for planning continuity.

## Archived Material

- `.archive/legacy/`: Legacy crawler experiments and superseded scripts.
- `.archive/manual-tests/`: Manual or ad hoc scripts that are not part of CI.

## Test Boundaries

- `backend/tests/` is the active backend test suite and is run by CI. Current baseline: `64 passed`.
- Frontend smoke validation is `npm run build` in `frontend/`; the build passes, with a known Vite large chunk warning.
- Company-data API smoke should use a temporary SQLite database under `.runtime/` so Excel import and CRUD checks do not mutate the default local database.
- Manual crawler/API experiments belong in `.archive/manual-tests/` unless promoted into a maintained test suite.

## Current Feature Surface

- Company data is maintained through `CompanyAsset` records in `backend/app/models/company.py`.
- Excel import is preview-confirm: `POST /api/company/import-excel/preview` parses without writing, and `POST /api/company/import-excel` confirms persistence.
- Company assets support manual create, update, soft delete, restore, and `include_deleted` queries.
- Matching evidence is persisted in `AnalysisResult.matching_details` and displayed by `frontend/src/components/AnalysisDetailModal.tsx`.

## Runtime and Generated Files

- `.runtime/`, `venv/`, `frontend/node_modules/`, generated databases, downloaded PDFs, attachments, and local logs are ignored.
- Runtime startup entrypoints are `scripts/start_mvp.ps1` for Windows and `scripts/start_mvp.sh` for Linux/WSL.
