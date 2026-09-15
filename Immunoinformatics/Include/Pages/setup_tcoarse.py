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

# Largest archive the upload endpoint accepts. The page refuses bigger files
# before sending them; this is what enforces it for any other client.
MAX_ARCHIVE_BYTES = 3 * 1024**3

# Slack on the request length check. The request carries the multipart
# boundaries and the flow_path field besides the archive, so its length is a
# few hundred bytes more than the file: without this, an archive just under
# the limit would be refused, with a message claiming it is over. The exact
# limit is enforced on the file itself once it has been read.
REQUEST_OVERHEAD_BYTES = 1024**2

MAX_ARCHIVE_MSG = (
    "The archive is larger than 3 GB. Put the predictions on the machine "
    "running Horus and browse to the folder instead."
)

# Largest total size the archive may unpack to. A small archive can still
# expand to fill the disk, so the members are added up before anything is
# written.
MAX_EXTRACTED_BYTES = int(3.5 * 1024**3)


def _check_extracted_size(sizes: typing.Iterable[int]) -> None:
    """
    Refuse an archive whose members add up to more than MAX_EXTRACTED_BYTES.
    """
    if sum(sizes) > MAX_EXTRACTED_BYTES:
        raise ValueError(
            "The archive unpacks to more than 3.5 GB. Put the predictions on the "
            "machine running Horus and browse to the folder instead."
        )


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

        # The declared sizes can be relied on: zipfile stops reading a member
        # at its declared size and fails the CRC check if the data is longer
        _check_extracted_size(info.file_size for info in zip_file.infolist())

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

        # Compression wraps the whole tar stream, so each member's size is the
        # number of bytes it really writes
        _check_extracted_size(member.size for member in tar_file.getmembers())

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
    from werkzeug.exceptions import RequestEntityTooLarge

    # Bound how much of the request is read before request.files parses, and
    # spools to disk, the body. Set on the request, Werkzeug refuses a longer
    # Content-Length up front and, for a chunked upload that sends no length at
    # all, stops reading once the limit is passed. Checking content_length by
    # hand misses that second case, which let the whole body be spooled first.
    # The allowance is for the form around the archive; the exact limit is
    # applied to the file below.
    request.max_content_length = MAX_ARCHIVE_BYTES + REQUEST_OVERHEAD_BYTES

    try:
        archive = request.files.get("archive")
        flow_path = request.form.get("flow_path")
    except RequestEntityTooLarge:
        return jsonify({"ok": False, "msg": MAX_ARCHIVE_MSG}), 413

    if archive is None or not archive.filename:
        return jsonify({"ok": False, "msg": "No archive was uploaded"}), 400

    # The exact limit, on the archive itself: the request length above includes
    # the form around it, and is not always sent (chunked uploads)
    archive.stream.seek(0, os.SEEK_END)
    archive_size = archive.stream.tell()
    archive.stream.seek(0)

    if archive_size > MAX_ARCHIVE_BYTES:
        return jsonify({"ok": False, "msg": MAX_ARCHIVE_MSG}), 413

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


# ==========================#
# Example set
# ==========================#
EXAMPLE_SET_DIR_NAME = "examples"


def _af3_model_folders(af3_dir: str) -> typing.List[str]:
    """
    The subfolders of `af3_dir` holding AlphaFold3 models, in the layout the
    Copy Models step reads: <tcr>/seed-*/*_model.cif.
    """
    import glob

    return [
        name
        for name in sorted(os.listdir(af3_dir))
        if os.path.isdir(os.path.join(af3_dir, name))
        and glob.glob(os.path.join(af3_dir, name, "seed-*", "*_model.cif"))
    ]


def _describe_example_set(tcoarse_dir: typing.Optional[str]) -> dict:
    """
    Whether the example set is usable from `tcoarse_dir`, and where it is.

    Kept apart from the endpoint so it can be checked without a running Horus.
    """
    if not tcoarse_dir:
        return {
            "ok": True,
            "available": False,
            "msg": "The TCoaRse installation folder is not configured",
        }

    af3_dir = os.path.join(str(tcoarse_dir).strip(), EXAMPLE_SET_DIR_NAME)

    if not os.path.isdir(af3_dir):
        return {"ok": True, "available": False, "msg": f"'{af3_dir}' does not exist"}

    folders = _af3_model_folders(af3_dir)

    if not folders:
        return {
            "ok": True,
            "available": False,
            "msg": f"'{af3_dir}' holds no AlphaFold3 models",
        }

    return {
        "ok": True,
        "available": True,
        "af3_dir": af3_dir,
        "folders": len(folders),
        "sample": folders[:5],
    }


def example_set():
    """
    Where the TCoaRse example set is on the machine running Horus, if it is there.

    The examples ship with the TCoaRse-nf checkout, so the folder is resolved
    from the configured TCoaRse installation instead of being hardcoded. That
    finds it on whichever machine the plugin is set up on -- perry, for the
    shared Horus server -- and reports it as unavailable anywhere else, so the
    page only offers it where it works.
    """
    from flask import jsonify

    try:
        from App import AppDelegate  # type: ignore

        config = AppDelegate().server.pluginManager.getPluginConfig("immuno", "Local")
    except Exception as error:  # pylint: disable=broad-exception-caught
        return jsonify(
            {
                "ok": True,
                "available": False,
                "msg": f"Could not read the TCoaRse configuration: {error}",
            }
        )

    return jsonify(_describe_example_set(config.get("tcoarse_dir")))


example_set_endpoint = PluginEndpoint(
    url="/tcoarse_api/example_set/", methods=["GET"], function=example_set
)

setup_tcoarse_page.addEndpoint(example_set_endpoint)
