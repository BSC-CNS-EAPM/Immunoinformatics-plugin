"""
The setup page of the TCoaRse pipeline block.

Besides the form, the page exposes an endpoint that takes an archive of the
AlphaFold3 predictions, extracts it into the flow folder and answers with the
folder the block should run on. That is the path for a Horus that is not
running on the machine holding the data; when it is, picking the folder is
cheaper and the form offers that too.
"""

import os
import typing

from HorusAPI import PluginEndpoint, PluginPage

# Define the Setup TCoaRse page
setup_tcoarse_page = PluginPage(
    id="tcoarse",
    name="Setup TCoaRse",
    description="Setup the TCoaRse pipeline",
    html="tcoarse.html",  # The HTML file to load
    hidden=True,
)

# Archives the upload endpoint accepts, longest suffix first so that
# ".tar.gz" is matched before ".gz" would be
ARCHIVE_SUFFIXES = (".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".tar", ".zip")

UPLOAD_DIR_NAME = "af3_upload"


def _is_within(directory: str, target: str) -> bool:
    """
    Whether `target` stays inside `directory` once resolved.
    """
    directory = os.path.realpath(directory)
    target = os.path.realpath(target)

    return target == directory or target.startswith(directory + os.sep)


def _safe_extract_zip(archive, destination: str) -> None:
    """
    Extract a zip, refusing members that would escape the destination.
    """
    import zipfile

    with zipfile.ZipFile(archive) as zip_file:
        for member in zip_file.namelist():
            if os.path.isabs(member) or not _is_within(
                destination, os.path.join(destination, member)
            ):
                raise ValueError(f"The archive holds an unsafe path: '{member}'")

        zip_file.extractall(destination)


def _safe_extract_tar(archive, destination: str) -> None:
    """
    Extract a tar, refusing members that would escape the destination.

    tarfile writes wherever a member says to, so "../../etc/x" or an absolute
    name would land outside the flow folder. Links are refused for the same
    reason: their target is not checked by the extraction itself.
    """
    import tarfile

    with tarfile.open(fileobj=archive) as tar_file:
        for member in tar_file.getmembers():
            if os.path.isabs(member.name) or not _is_within(
                destination, os.path.join(destination, member.name)
            ):
                raise ValueError(f"The archive holds an unsafe path: '{member.name}'")

            if member.issym() or member.islnk():
                raise ValueError(f"The archive holds a link: '{member.name}'")

        tar_file.extractall(destination)


def _af3_root(extracted: str) -> str:
    """
    The folder the pipeline should run on, inside what was extracted.

    An archive is made either from the folder ("af3_outputs/tcr_1/...") or from
    its contents ("tcr_1/..."). When everything sits under a single directory,
    that directory is the root; otherwise what was extracted already is.
    """
    entries = [name for name in os.listdir(extracted) if not name.startswith(".")]

    if len(entries) == 1:
        only = os.path.join(extracted, entries[0])
        if os.path.isdir(only):
            return only

    return extracted


def upload_af3():
    """
    Take an archive of the AF3 predictions and extract it into the flow folder.
    """
    import shutil

    from flask import jsonify, request

    archive = request.files.get("archive")
    flow_path = request.form.get("flow_path")

    if archive is None or not archive.filename:
        return jsonify({"ok": False, "msg": "No archive was uploaded"}), 400

    filename = os.path.basename(archive.filename)
    suffix = next(
        (s for s in ARCHIVE_SUFFIXES if filename.lower().endswith(s)),
        None,
    )

    if suffix is None:
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": (
                        f"'{filename}' is not an archive. Upload one of: "
                        + ", ".join(ARCHIVE_SUFFIXES)
                    ),
                }
            ),
            400,
        )

    if not flow_path:
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": "Save the flow before uploading, so the archive has somewhere to go",
                }
            ),
            400,
        )

    try:
        from Server.FlowManager import Flow  # type: ignore

        work_dir = Flow.flowWorkDir(flow_path)

        destination = os.path.join(work_dir, UPLOAD_DIR_NAME)

        # A second upload replaces the first, so a corrected archive does not
        # get merged into whatever the previous one left behind
        if os.path.exists(destination):
            shutil.rmtree(destination)

        os.makedirs(destination, exist_ok=True)

        if suffix == ".zip":
            _safe_extract_zip(archive.stream, destination)
        else:
            _safe_extract_tar(archive.stream, destination)

        af3_dir = _af3_root(destination)

        folders = [
            name
            for name in sorted(os.listdir(af3_dir))
            if os.path.isdir(os.path.join(af3_dir, name))
        ]

        return jsonify(
            {
                "ok": True,
                "af3_dir": af3_dir,
                "folders": len(folders),
                "sample": folders[:5],
            }
        )

    except Exception as error:  # pylint: disable=broad-exception-caught
        return jsonify({"ok": False, "msg": str(error)}), 400


upload_af3_endpoint = PluginEndpoint(
    url="/tcoarse_api/upload_af3/", methods=["POST"], function=upload_af3
)

setup_tcoarse_page.addEndpoint(upload_af3_endpoint)
