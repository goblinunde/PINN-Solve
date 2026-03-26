# Repository Guidelines

## Project Structure & Module Organization
`pinn-core/` contains the Rust solver exposed to Python through PyO3. Keep numerical logic in `src/autodiff`, `src/nn`, `src/numerics`, `src/solver`, `src/gpu`, and `src/bindings`. `backend/` hosts the FastAPI service: routes live in `backend/api/`, task wiring in `backend/tasks/`, data models in `backend/data/`, and preprocessing/postprocessing helpers in their matching folders. `frontend/` is a Vite + Vue 3 app with pages in `frontend/src/views/`, reusable charts/components in `frontend/src/components/`, routing in `src/router/`, state in `src/store/`, and translations in `src/locales/`. Use `examples/` for sample PDE configs and `docs/` for architecture and quickstart notes.

## Build, Test, and Development Commands
- `cd pinn-core && PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 cargo build --release`: build the Rust extension used by Python.
- `cd backend && source .venv/bin/activate && python main.py`: start FastAPI on `http://localhost:8000`.
- `cd frontend && npm install && npm run dev`: start the UI on `http://localhost:38000`.
- `./start-dev.sh`: launch backend and frontend together for local development.
- `./test-api.sh`: smoke-test `/health` and `/api/train/`.
- `python test_features.py`: run end-to-end feature checks against the compiled `pinn_core` module.

## Coding Style & Naming Conventions
Match the existing file style. Python uses 4-space indentation, `snake_case`, and small focused modules. Vue and JavaScript use 2-space indentation, ES module imports, and PascalCase component filenames such as `ConfigView.vue` and `LossChart.vue`. Rust modules and files should stay `snake_case`; types stay `CamelCase`. No formatter or linter config is committed yet, so keep changes consistent with nearby code and avoid broad style-only edits.

## Testing Guidelines
Place new Python tests in `tests/` or add targeted repo-root regression scripts when they exercise multiple layers. Name Python tests `test_*.py`. If you change API behavior, update `test-api.sh` or add an equivalent reproducible check. For frontend changes, include manual verification steps because there is no frontend test harness in the repo today.

## Commit & Pull Request Guidelines
Recent history favors short, imperative subjects and often uses Conventional Commit prefixes such as `feat:` and `test:`. Prefer `type: concise summary`, for example `feat: add poisson boundary presets`. Keep pull requests scoped to one feature or layer when possible. PR descriptions should state the purpose, list affected directories, include commands run, and attach screenshots for UI changes. Link the related issue or task when one exists.
