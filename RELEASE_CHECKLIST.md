# ShikariMCP Release Checklist

## Pre-Release

### Code Quality

- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] Tests pass on Python 3.11, 3.12, 3.13
- [ ] Shellcheck passes on all scripts: `shellcheck scripts/*.sh`
- [ ] No linting warnings or errors
- [ ] Code follows project conventions

### Documentation

- [ ] README.md is up to date
- [ ] MCP client docs are current (`docs/MCP_CLIENTS.md`)
- [ ] Profile documentation is accurate
- [ ] Sample reports reflect current output format
- [ ] Changelog updated with release notes

### Security

- [ ] Auth is required by default for HTTP transport
- [ ] No secrets or API keys in code or docs
- [ ] `.env.example` has safe defaults
- [ ] `.gitignore` excludes sensitive files
- [ ] Audit logging is enabled by default
- [ ] Target allowlist is documented

### Tooling

- [ ] `tools.lock.json` is up to date with latest pinned versions
- [ ] Core profile tools verify successfully
- [ ] Installer scripts work on fresh Ubuntu/Kali
- [ ] Docker images build successfully
- [ ] Docker smoke test passes

### Manifest

- [ ] All promoted tools have manifest entries
- [ ] Parser coverage matches manifest tools
- [ ] Tool descriptions are accurate
- [ ] Risk classes are correctly assigned

## Release Process

### Version Bump

```bash
# Update version in pyproject.toml
# Update version label in Dockerfiles
# Tag the release
git tag -a v0.X.0 -m "Release v0.X.0"
git push origin v0.X.0
```

### Build Verification

```bash
# Build the production core image
docker build -t shikari-mcp:latest -f docker/Dockerfile .
docker build -t shikari-mcp:core -f docker/Dockerfile.core .

# Run verification
docker run --rm --entrypoint shikari-mcp shikari-mcp:core \
  tools verify --profile core --json
```

### Test Installation

```bash
# Fresh install test
pip install .
shikari-mcp --transport stdio

# Or with uv
uv sync
uv run shikari-mcp --transport stdio
```

### GitHub Release

- [ ] Create release on GitHub with tag
- [ ] Add release notes (changelog summary)
- [ ] Attach Docker image digests
- [ ] Mark as pre-release if needed

## Post-Release

- [ ] Verify PyPI package (if publishing)
- [ ] Test Docker Hub images (if publishing)
- [ ] Update documentation links
- [ ] Notify users of breaking changes
- [ ] Monitor issues for regressions

## Emergency Rollback

If critical issues are discovered:

1. Yank the release on PyPI (if applicable)
2. Mark release as draft on GitHub
3. Issue hotfix with `v0.X.1`
4. Communicate changes to users
