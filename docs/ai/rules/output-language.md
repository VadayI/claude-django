# Output language

Honor the user's current language preference. Read the project-owned shared
preference `docs/ai/overrides/output-language.md` when present; an unmigrated
legacy `.claude/rules/output-language.md` stays readable until
`python scripts/ai/project_state.py --root . --language --apply` moves it and
leaves a pointer. Never overwrite either file on update, and write new
preferences only to the shared file. If neither the session nor project
declares a preference, ask once.
