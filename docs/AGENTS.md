# Repository Guidelines

## Project Structure & Module Organization

This repository is the documentation root for the Yacht dice game project. Currently it contains a single specification file.

- game-rules.md -- Complete rule specification for the Yacht dice game, including categories, scoring formulas, turn flow, and implementation notes.

As the project grows, planned structure:

- src/ -- Application source code (game engine, UI, utilities)
- tests/ -- Unit and integration tests
- assets/ -- Images, icons, and static media
- docs/ -- Extended documentation (this repo serves as the initial docs root)

## Build, Test, and Development Commands

No build system or test framework is configured yet. When implementation begins, commands will be documented here. Typical patterns to follow:

- npm test or python -m pytest -- run the test suite
- npm run build or cargo build -- compile or bundle the application
- npm start or python src/main.py -- run locally for development

## Coding Style & Naming Conventions

- Use 2-space indentation for all languages unless the chosen language convention dictates otherwise (e.g., Python follows PEP 8 with 4 spaces).
- Use snake_case for filenames, camelCase or snake_case for variables/functions depending on the primary language chosen.
- Keep functions and modules focused on a single responsibility.
- Run the configured formatter or linter before committing (tool TBD once the language is selected).

## Testing Guidelines

When tests are added:

- Use a standard test framework for the chosen language (pytest for Python, Jest for JavaScript, etc.).
- Name test files with a test_ prefix or suffix (e.g., test_scoring.py, scoring.test.js).
- Cover all 12 scoring categories and edge cases (invalid rolls, skipped turns, score override to zero).
- Target minimum 80% line coverage.
- Run the full suite before opening a pull request.

## Commit and Pull Request Guidelines

- Write commit messages in the imperative mood: "Add scoring logic for Yacht category" rather than "Added scoring...".
- Reference the relevant game category or feature area in the subject line when possible.
- Pull requests must include a description of changes, affected files, and any visual or behavioral impact.
- If changes modify game rules or scoring, link back to the section in game-rules.md that was updated or implemented.
- Self-review your diff and confirm tests pass before requesting review.

## Agent-Specific Instructions

- Always read game-rules.md before implementing scoring or turn logic; it is the source of truth for game mechanics.
- Do not modify game-rules.md without explicit approval from the project owner.
- When adding new files, follow the planned directory structure above.
- Prefer minimal, focused changes over broad refactors.



## Conversation & Work Rules for Agents

- Do not use emojis in any output or messages.
- Do not use # as decorative formatting; the environment is CLI-based. Markdown headings are allowed only in document files.
- Before installing any package, tool, or system dependency, always ask the user for confirmation first. Do not proceed without explicit approval.
- Prefer installing packages locally into the current working directory (e.g., local virtual environments, workspace-level dependencies) rather than globally.
- Keep responses concise and direct. Avoid unnecessary verbosity.
