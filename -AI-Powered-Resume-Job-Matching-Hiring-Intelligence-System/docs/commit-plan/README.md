# Commit Plan Usage Guide

This folder helps you maintain a clean 30-day GitHub contribution streak.

## Files in this folder
- `30-day-commit-plan.md` → day-by-day work plan.
- `daily-commit-log.md` → daily record tracker (update after each push).

## One-time setup
From project root:

```powershell
git init
git remote add origin https://github.com/sumitaiml/-AI-Powered-Resume-Job-Matching-Hiring-Intelligence-System.git
```

If remote already exists:

```powershell
git remote set-url origin https://github.com/sumitaiml/-AI-Powered-Resume-Job-Matching-Hiring-Intelligence-System.git
```

## Daily workflow (repeat for 30 days)
```powershell
# 1) make your planned day change
# 2) stage files
git add .

# 3) commit (example for Day 01)
git commit -m "Day 01: docs - initialize 30-day commit plan and tracking log"

# 4) push
git push -u origin main
```

## Record maintenance
After pushing each day:
1. Open `daily-commit-log.md`.
2. Fill that day row: date, focus area, commit message, files changed, commit URL.
3. Set status to ✅ Done.

## Good commit rules
- Keep one focused objective per day.
- Avoid empty/no-change commits.
- Prefer real improvements: code, tests, docs, refactor, bug fix.
- Keep messages clear and searchable.
