from __future__ import annotations

import hashlib
import shutil
import tarfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

from pmanager.libraries import LibraryRecipe, get_library
from pmanager.paths import ProjectPaths


class FetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchPlan:
    library: LibraryRecipe
    url: str
    archive_path: Path
    extract_root: Path
    target_dir: Path
    sha256: str | None = None


def vtk_source_url(version: str) -> str:
    return f"https://gitlab.kitware.com/vtk/vtk/-/archive/v{version}/vtk-v{version}.tar.gz?ref_type=tags"


def archive_name_from_url(url: str, fallback: str) -> str:
    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name
    return name or fallback


def plan_fetch_vtk(
    *,
    paths: ProjectPaths | None = None,
    url: str | None = None,
    sha256: str | None = None,
) -> FetchPlan:
    paths = paths or ProjectPaths.discover()
    library = get_library("vtk")
    source_url = url or vtk_source_url(library.version)
    archive_name = archive_name_from_url(source_url, f"{library.source_dir_name}.tar.gz")
    downloads_dir = paths.root / ".tmp" / "downloads"
    return FetchPlan(
        library=library,
        url=source_url,
        archive_path=downloads_dir / archive_name,
        extract_root=downloads_dir / f"extract-{library.source_dir_name}",
        target_dir=paths.source_root / library.source_dir_name,
        sha256=sha256,
    )


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(path: Path, expected: str | None) -> None:
    if not expected:
        return
    actual = sha256_file(path)
    if actual.lower() != expected.lower():
        raise FetchError(f"Checksum mismatch for {path}: expected {expected}, got {actual}")


def _safe_member_path(destination: Path, member_name: str) -> Path:
    normalized = PurePosixPath(member_name.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise FetchError(f"Unsafe archive member path: {member_name}")

    target = (destination / Path(*normalized.parts)).resolve(strict=False)
    destination_resolved = destination.resolve(strict=False)
    try:
        target.relative_to(destination_resolved)
    except ValueError as exc:
        raise FetchError(f"Archive member escapes extraction root: {member_name}") from exc
    return target


def safe_extract_zip(archive_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            _safe_member_path(destination, info.filename)
        archive.extractall(destination)


def safe_extract_tar(archive_path: Path, destination: Path) -> None:
    with tarfile.open(archive_path) as archive:
        for member in archive.getmembers():
            _safe_member_path(destination, member.name)
            if member.issym() or member.islnk():
                raise FetchError(f"Refusing archive link member: {member.name}")
        archive.extractall(destination)


def safe_extract_archive(archive_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    suffixes = "".join(archive_path.suffixes).lower()
    if suffixes.endswith(".zip"):
        safe_extract_zip(archive_path, destination)
        return
    if suffixes.endswith(".tar.gz") or suffixes.endswith(".tgz") or suffixes.endswith(".tar"):
        safe_extract_tar(archive_path, destination)
        return
    raise FetchError(f"Unsupported archive type: {archive_path}")


def single_extracted_directory(extract_root: Path) -> Path:
    directories = [path for path in extract_root.iterdir() if path.is_dir()]
    if len(directories) != 1:
        raise FetchError(f"Expected exactly one extracted source directory under {extract_root}")
    return directories[0]


def fetch_vtk(
    *,
    paths: ProjectPaths | None = None,
    url: str | None = None,
    sha256: str | None = None,
    force: bool = False,
    verbose: bool = False,
) -> Path:
    plan = plan_fetch_vtk(paths=paths, url=url, sha256=sha256)

    if plan.target_dir.exists() and not force:
        raise FetchError(f"Target directory already exists: {plan.target_dir}. Use --force to replace it.")

    if plan.archive_path.exists():
        plan.archive_path.unlink()
    if plan.extract_root.exists():
        shutil.rmtree(plan.extract_root)

    if verbose:
        print(f"Fetching {plan.library.name} {plan.library.version}")
        print(f"URL:      {plan.url}")
        print(f"Archive:  {plan.archive_path}")
    download_file(plan.url, plan.archive_path)
    if verbose:
        print("Download complete.")
        if plan.sha256:
            print("Verifying SHA256...")
    verify_sha256(plan.archive_path, plan.sha256)
    if verbose and plan.sha256:
        print("Checksum OK.")
    if verbose:
        print(f"Extracting to {plan.extract_root}...")
    safe_extract_archive(plan.archive_path, plan.extract_root)

    extracted = single_extracted_directory(plan.extract_root)
    plan.target_dir.parent.mkdir(parents=True, exist_ok=True)
    if plan.target_dir.exists():
        if verbose:
            print(f"Replacing existing source tree: {plan.target_dir}")
        shutil.rmtree(plan.target_dir)
    if verbose:
        print(f"Moving source tree into {plan.target_dir}...")
    shutil.move(str(extracted), str(plan.target_dir))
    shutil.rmtree(plan.extract_root)
    if verbose:
        print("Fetch complete.")
    return plan.target_dir
