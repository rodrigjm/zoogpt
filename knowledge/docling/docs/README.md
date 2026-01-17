# Documentation Structure

## Directory Layout

```
docs/
├── ProjectPlan.md          # 📋 Master tracker (deployment, features, bugs, roadmap)
├── README.md               # This file
├── ARCHITECTURE.md         # System architecture overview
├── DEPLOYMENT.md           # Deployment procedures
├── QUICK_START.md          # Getting started guide
├── CLOUDFLARE_TUNNEL_SETUP.md  # SSL/tunnel configuration
│
├── active/                 # 🔄 ONGOING WORK
│   ├── _TEMPLATE/          # Template for new features
│   └── <feature-name>/     # One directory per active feature
│       ├── README.md       # Feature overview & progress
│       ├── design.md       # Technical design
│       ├── implementation.md
│       └── qa-report.md
│
└── archive/                # ✅ COMPLETED WORK
    ├── <feature-docs>.md   # Historical documentation
    └── ...                 # Reference material
```

## Workflow

### Starting a New Feature
1. Copy `docs/active/_TEMPLATE/` to `docs/active/<feature-name>/`
2. Update `docs/ProjectPlan.md` → "Active Features" section
3. Work in the feature directory, updating progress

### Completing a Feature
1. Move `docs/active/<feature-name>/` → `docs/archive/<feature-name>/`
2. Update `docs/ProjectPlan.md`:
   - Remove from "Active Features"
   - Add to "Completed (Recent)" with link to archive
3. Update any roadmap items as complete

### Bug Tracking
- Log bugs in `docs/ProjectPlan.md` → "Bugs & Issues" table
- Link to relevant code or docs
- Remove when resolved

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Feature docs | `kebab-case` | `voice-streaming/` |
| Reports | `TYPE_YYYY-MM-DD.md` | `QA_REPORT_2026-01-15.md` |
| Specs | `UPPER_SNAKE_CASE.md` | `DESIGN_SPEC.md` |

## Quick Reference

- **What's deployed?** → `ProjectPlan.md` → "Current Deployment"
- **What's being built?** → `ProjectPlan.md` → "Active Features" or `docs/active/`
- **What's planned?** → `ProjectPlan.md` → "Roadmap"
- **Past features?** → `docs/archive/`
