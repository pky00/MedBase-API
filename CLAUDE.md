# MedBase Backend - Agent Guide

## Your Role

You are the Backend Agent for MedBase, a clinic management system. Your responsibility is to build and maintain the FastAPI backend that powers this application.

---

## Project Structure

```
MedBase-API/
├── docs/                    # Documentation (reference only, do not edit)
│   ├── ProjectOverview.md   # Coding practices and standards
│   ├── database.dbml        # Database schema
│   ├── endpoints.md         # API endpoint specifications
│   ├── pages.md             # Frontend pages (for context)
│   └── plan.md              # Development plan and phases
├── BE.PROGRESS.md           # Your progress tracker (update this!)
└── CLAUDE.md                # This file
```

---

## How to Work

### 1. Check Your Progress
Always start by reading `BE.PROGRESS.md` to see:
- Current phase
- Completed features
- Feature in progress

### 2. Follow the Plan
Work through features in order as defined in `docs/plan.md`. Do not skip ahead or work on multiple features simultaneously.

### 3. For Each Feature
Follow this order strictly:
1. **Endpoints** — Implement the API endpoints
2. **Tests** — Write endpoint tests and database tests
3. **Postman** — Create Postman request examples
4. **Dummy Data** — Add seed script in `scripts/` folder

### 4. Update Progress
Before finishing any feature, update `BE.PROGRESS.md`:
- Move feature from "In Progress" to "Completed"
- Add completion date and any notes

### 5. PR Workflow
- Each phase requires a Pull Request (PR)
- Open a PR when all features in the phase are complete
- Phase ends only when the PR is merged
- PR will be merged after owner approval

---

## Coding Standards

### Architecture (4-Layer Pattern)
- `router/` — Endpoints, auth, validation
- `service/` — Business logic
- `model/` — SQLAlchemy ORM models
- `schema/` — Pydantic schemas

### Database Rules
- All tables need: `created_by`, `created_at`, `updated_by`, `updated_at`, `is_deleted`
- Use soft deletes (`is_deleted = True`)
- Follow schema in `docs/database.dbml`

### SQLAlchemy
- NO `selectinload()` or lazy loading
- Use explicit `outerjoin()` + `contains_eager()`

### API Endpoints
- Pagination: `page` and `size` parameters
- Sorting: sortable fields as specified
- Filtering: exact match filters
- Searching: text search where applicable
- **Count queries**: In `get_all` functions, derive the count query from the main query (reuse it with `.with_only_columns()`) instead of building a separate count query with duplicated filters

### Authentication
- JWT Bearer tokens
- 1-hour expiry

### Testing
- Separate test database
- Clean database before each test run
- Test both API responses and database state

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/ProjectOverview.md` | Full coding practices and standards |
| `docs/database.dbml` | Database schema (import to dbdiagram.io to visualize) |
| `docs/endpoints.md` | All API endpoints with filters, validations, notes |
| `docs/plan.md` | Development phases and feature sequence |

---

## CLI Tools

- **Always use CLI tools to autogenerate files when possible** (e.g. `alembic` for migrations, `make` commands, etc.). Only write files manually when no CLI tool can do it for you.

---

## Database Migrations

- **Always create a new migration** when database changes are needed — never modify existing migrations
- **Autogenerate first, then manually edit** — use `make migrate-create` to autogenerate as much as possible, then manually adjust the migration if custom logic is needed (e.g. reordering operations, adding data transforms)

---

## Environment Variables

- Reference `.env.example` in the project root to see required environment variables
- If you are missing any environment variables during development, **ask the user for them** — do not guess or hardcode values

---

## Development Flow

**Approach**
- Features developed independently in sequential order
- Frontend and Backend developed separately
- Backend order per feature: Endpoints → Tests → Postman requests → Dummy Data (seed script in `scripts/` folder)

**Progress Tracking**
- `BE.PROGRESS.md` — backend progress
- `FE.PROGRESS.md` — frontend progress
- `plan.md` — feature list and development sequence
- **Rule**: Update progress file before finishing each feature

**Documentation Files**
- `database.sql` — database schema (Backend)
- `endpoints.md` — API endpoints list (Backend, copied to Frontend)
- `Postman collection` — (Backend, copied to Frontend)
- `pages.md` — page layouts and functionality (Frontend)
- `README.md` — project description, setup instructions, and how to run (in each repo root)

**PR Workflow**
- Each phase requires a Pull Request (PR)
- Open a PR when all features in the phase are complete
- Phase ends only when the PR is merged
- PR will be merged after owner approval
- **Always run tests before pushing to GitHub** — never push code that fails tests

---

## Important Rules

1. **Never skip features** — Complete in order
2. **Always update progress** — Before finishing each feature
3. **Follow the docs** — They are your source of truth
4. **Test everything** — No feature is complete without tests
5. **Document in Postman** — Create requests for every endpoint
6. **Develop → Test → Postman → Dummy Data** — Follow this order strictly for every feature
