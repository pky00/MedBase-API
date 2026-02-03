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

### 4. Update Progress
Before finishing any feature, update `BE.PROGRESS.md`:
- Move feature from "In Progress" to "Completed"
- Add completion date and any notes

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

## Important Rules

1. **Never skip features** — Complete in order
2. **Always update progress** — Before finishing each feature
3. **Follow the docs** — They are your source of truth
4. **Test everything** — No feature is complete without tests
5. **Document in Postman** — Create requests for every endpoint
