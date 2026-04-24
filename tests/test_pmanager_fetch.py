from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

from typer.testing import CliRunner

from pmanager.cli import app
from pmanager.fetch import FetchError, fetch_vtk, plan_fetch_vtk, safe_extract_archive, sha256_file
from pmanager.paths import ProjectPaths


def make_zip_archive(path: Path, root_name: str = "vtk-v9.3.1") -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{root_name}/README.md", "vtk source")


def make_tar_archive(path: Path, root_name: str = "vtk-v9.3.1") -> None:
    data = b"vtk source"
    info = tarfile.TarInfo(f"{root_name}/README.md")
    info.size = len(data)
    with tarfile.open(path, "w:gz") as archive:
        archive.addfile(info, io.BytesIO(data))


def test_plan_fetch_vtk_uses_repo_layout(tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    plan = plan_fetch_vtk(paths=paths)

    assert plan.library.name == "vtk"
    assert plan.archive_path.parent == tmp_path / ".tmp" / "downloads"
    assert plan.extract_root == tmp_path / ".tmp" / "downloads" / "extract-vtk-9.3.1"
    assert plan.target_dir == tmp_path / "external" / "src" / "vtk-9.3.1"


def test_fetch_vtk_from_local_zip_url(tmp_path: Path) -> None:
    archive = tmp_path / "vtk-v9.3.1.zip"
    make_zip_archive(archive)
    paths = ProjectPaths(root=tmp_path / "repo")

    target = fetch_vtk(
        paths=paths,
        url=archive.as_uri(),
        sha256=sha256_file(archive),
    )

    assert target == paths.vtk_source_dir()
    assert (target / "README.md").read_text(encoding="utf-8") == "vtk source"


def test_fetch_vtk_from_local_tar_url(tmp_path: Path) -> None:
    archive = tmp_path / "vtk-v9.3.1.tar.gz"
    make_tar_archive(archive)
    paths = ProjectPaths(root=tmp_path / "repo")

    target = fetch_vtk(paths=paths, url=archive.as_uri(), sha256=sha256_file(archive))

    assert (target / "README.md").exists()


def test_fetch_vtk_refuses_existing_target_without_force(tmp_path: Path) -> None:
    archive = tmp_path / "vtk-v9.3.1.zip"
    make_zip_archive(archive)
    paths = ProjectPaths(root=tmp_path / "repo")
    paths.vtk_source_dir().mkdir(parents=True)

    try:
        fetch_vtk(paths=paths, url=archive.as_uri())
    except FetchError as exc:
        assert "Use --force" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("fetch_vtk should refuse an existing target without force")


def test_safe_extract_zip_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../evil.txt", "nope")

    try:
        safe_extract_archive(archive, tmp_path / "extract")
    except FetchError as exc:
        assert "Unsafe archive member path" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("archive traversal should be rejected")


def test_safe_extract_tar_rejects_link_members(tmp_path: Path) -> None:
    archive = tmp_path / "bad.tar.gz"
    link = tarfile.TarInfo("vtk-v9.3.1/link")
    link.type = tarfile.SYMTYPE
    link.linkname = "README.md"
    with tarfile.open(archive, "w:gz") as tf:
        tf.addfile(link)

    try:
        safe_extract_archive(archive, tmp_path / "extract")
    except FetchError as exc:
        assert "Refusing archive link member" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("archive links should be rejected")


def test_fetch_vtk_cli_with_local_archive(tmp_path: Path, monkeypatch) -> None:
    archive = tmp_path / "vtk-v9.3.1.zip"
    make_zip_archive(archive)
    repo = tmp_path / "repo"

    monkeypatch.setattr("pmanager.fetch.ProjectPaths.discover", classmethod(lambda cls: ProjectPaths(repo)))

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["fetch", "vtk", "--url", archive.as_uri(), "--sha256", sha256_file(archive)],
    )

    assert result.exit_code == 0
    assert "Fetched vtk 9.3.1 source" in result.stdout
    assert (repo / "external" / "src" / "vtk-9.3.1" / "README.md").exists()
