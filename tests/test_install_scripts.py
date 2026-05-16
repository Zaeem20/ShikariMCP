from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_install_tools_dry_run_is_non_mutating():
    script = (ROOT / "scripts" / "install-tools.sh").read_text(encoding="utf-8")

    assert "DRY_RUN=false" in script
    assert "--dry-run" in script
    assert 'if [[ "$DRY_RUN" != "true" ]]' in script
    assert "Dry-run complete; verification was skipped." in script


def test_install_tools_supports_profiles_and_macos_best_effort():
    script = (ROOT / "scripts" / "install-tools.sh").read_text(encoding="utf-8")

    for profile in ("core", "recon", "web", "cloud", "forensics", "offensive", "full"):
        assert profile in script

    assert 'OS_NAME="$(uname -s)"' in script
    assert "IS_MACOS=true" in script
    assert "brew install" in script
    assert "continuing best-effort" in script
