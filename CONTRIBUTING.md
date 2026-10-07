# OutreachAI - Contributing Guide

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch: `git checkout -b feature/my-feature`
4. Follow the development setup in SETUP.md

## Development Workflow

### Backend

1. **Code Style**
   ```bash
   # Format code
   black app/
   
   # Lint code
   flake8 app/
   
   # Type checking
   mypy app/
   ```

2. **Testing**
   ```bash
   # Run tests
   pytest
   
   # With coverage
   pytest --cov=app
   ```

3. **Commit**
   ```bash
   git add .
   git commit -m "feat: add new agent capability"
   ```

### Frontend

1. **Code Style**
   ```bash
   npm run lint
   npm run format
   ```

2. **Testing**
   ```bash
   npm test
   ```

3. **Build**
   ```bash
   npm run build
   ```

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add new feature`
- `fix: fix a bug`
- `docs: update documentation`
- `style: format code`
- `refactor: refactor code`
- `test: add tests`
- `chore: maintenance`

## Pull Request Process

1. Update CHANGELOG.md
2. Update documentation if needed
3. Ensure tests pass
4. Get 2 approvals before merge
5. Squash commits if needed

## Reporting Bugs

Include:
- Detailed description
- Steps to reproduce
- Expected vs actual behavior
- Logs/screenshots
- Environment (OS, Python/Node version)

## Feature Requests

Include:
- Use case
- Proposed implementation
- Potential impact
- Examples

---

Thank you for contributing! 🚀
