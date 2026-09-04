import os
from HorusAPI import PluginPage, PluginEndpoint
import typing

results_page = PluginPage(
    id="results",
    name="PredIG results",
    description="View the PredIG results",
    html="results.html",  # The HTML file to load
    hidden=True,
)

def _csv_meta_cache_path(full_csv: str) -> str:
    return full_csv + ".pagemeta.json"


def _load_csv_meta(full_csv: str, stat: "os.stat_result"):
    """
    Read cached (columns, total_rows) for full_csv if a sidecar cache file
    exists and still matches the file's mtime/size, else None.

    Each request runs in its own forked subprocess (Server.PluginManager
    SubprocessManager.subprocessCall), so an in-memory cache would not
    survive between requests; the cache is persisted to disk instead.
    """

    import json

    cache_path = _csv_meta_cache_path(full_csv)
    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, "r") as f:
            meta = json.load(f)
    except (OSError, ValueError):
        return None

    if meta.get("mtime") != stat.st_mtime or meta.get("size") != stat.st_size:
        return None

    return meta.get("columns"), meta.get("total_rows")


def _save_csv_meta(full_csv: str, stat: "os.stat_result", columns: list, total_rows: int):
    import json

    meta = {
        "mtime": stat.st_mtime,
        "size": stat.st_size,
        "columns": columns,
        "total_rows": total_rows,
    }
    try:
        with open(_csv_meta_cache_path(full_csv), "w") as f:
            json.dump(meta, f)
    except OSError:
        pass


def return_data():

    from flask import request, Response, send_file, jsonify

    data: dict = request.args

    csv: typing.Union[str, None] = data.get("csv")

    if not csv:
        return Response("No csv provided", status=400)

    full_csv = csv

    from App import AppDelegate  # type: ignore

    if AppDelegate().mode == "webapp":
        from flask_login import current_user
        from Server.FileExplorer import UserFileExplorer  # type: ignore

        # Get current user path
        full_csv: str = UserFileExplorer(csv, current_user).getAbsolutePath()
    else:
        full_csv = csv

    if (
        not os.path.exists(full_csv)
        or not os.path.isfile(full_csv)
        or not csv.endswith(".csv")
    ):
        return Response("Results do not exist", status=400)

    import pandas as pd
    import numpy as np
    import math

    try:
        stat = os.stat(full_csv)
        cached = _load_csv_meta(full_csv, stat)
        if cached:
            columns, total_rows = cached
        else:
            # Read header only to get column names
            columns = list(pd.read_csv(full_csv, nrows=0).columns)

            # Count total rows efficiently without loading entire file into memory
            with open(full_csv, "rb") as f:
                total_rows = max(0, sum(1 for line in f if line.strip()) - 1)

            _save_csv_meta(full_csv, stat, columns, total_rows)

        # Parse pagination parameters
        try:
            page = max(1, int(data.get("page", 1)))
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = max(1, min(10000, int(data.get("page_size", data.get("limit", 100)))))
        except (ValueError, TypeError):
            page_size = 100

        total_pages = math.ceil(total_rows / page_size) if total_rows > 0 else 1
        skip_count = (page - 1) * page_size

        if total_rows == 0 or skip_count >= total_rows:
            data_dict = []
        else:
            df = pd.read_csv(
                full_csv,
                skiprows=range(1, skip_count + 1),
                nrows=page_size
            )
            # Replace all NaN values with None
            df = df.replace({np.nan: None})
            data_dict = df.to_dict(orient="records")

        return jsonify({
            "ok": True,
            "results": data_dict,
            "columns": columns,
            "total": total_rows,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        })

    except Exception as e:
        return Response(str(e), status=400)


results_data_endpoint = PluginEndpoint(
    url="/results_api/results/", methods=["GET"], function=return_data
)

results_page.addEndpoint(results_data_endpoint)


def download_results():
    from flask import request, Response, send_file, after_this_request

    data: dict = request.args

    csv: typing.Union[str, None] = data.get("csv")
    simulation: typing.Union[str, None] = data.get("simulation")
    name: typing.Union[str, None] = data.get("name")

    if not csv:
        return Response("No csv provided", status=400)

    full_csv = csv

    from App import AppDelegate  # type: ignore

    if AppDelegate().mode == "webapp":
        from flask_login import current_user
        from Server.FileExplorer import UserFileExplorer  # type: ignore

        # Get current user path
        full_csv: str = UserFileExplorer(csv, current_user).getAbsolutePath()
    else:
        full_csv = csv

    if (
        not os.path.exists(full_csv)
        or not os.path.isfile(full_csv)
        or not csv.endswith(".csv")
    ):
        return Response("CSV does not exist", status=400)

    import pandas as pd

    download_name: typing.Union[str, None] = None
    if simulation:
        folder_to_download = os.path.dirname(full_csv)
        folder_name = os.path.basename(folder_to_download)
        full_zip_path = os.path.join(os.path.dirname(folder_to_download), folder_name)
        full_zip_path_with_extension = full_zip_path + ".zip"

        # Compress the folder
        if os.path.exists(full_zip_path_with_extension):
            os.remove(full_zip_path_with_extension)

        import shutil

        os.chdir(folder_to_download)
        shutil.make_archive(
            full_zip_path,
            "zip",
            root_dir=folder_to_download,
        )

        download_name = name + ".zip" if name else None

        full_zip_path = full_zip_path_with_extension

        @after_this_request
        def remove_file(response):
            if os.path.exists(full_zip_path_with_extension):
                os.remove(full_zip_path_with_extension)

    else:
        # Download the csv
        full_zip_path = full_csv
        download_name = name + ".csv" if name else None

    return send_file(full_zip_path, as_attachment=True, download_name=download_name)


download_results_endpoint = PluginEndpoint(
    url="/results_api/download_results/", methods=["GET"], function=download_results
)


results_page.addEndpoint(download_results_endpoint)


def _demo_csv_meta_cache():
    """Self-check: sidecar cache hits on unchanged file, invalidates on modification."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("a,b\n1,2\n3,4\n")
        path = f.name

    cache_path = _csv_meta_cache_path(path)
    try:
        assert not os.path.exists(cache_path)
        assert _load_csv_meta(path, os.stat(path)) is None

        stat1 = os.stat(path)
        _save_csv_meta(path, stat1, ["a", "b"], 2)
        assert os.path.exists(cache_path)
        assert _load_csv_meta(path, stat1) == (["a", "b"], 2)

        with open(path, "a") as f:
            f.write("5,6\n")
        os.utime(path, (stat1.st_mtime + 10, stat1.st_mtime + 10))
        stat2 = os.stat(path)
        assert _load_csv_meta(path, stat2) is None, (
            "cache must invalidate when file mtime/size changes"
        )
        print("ok")
    finally:
        os.remove(path)
        if os.path.exists(cache_path):
            os.remove(cache_path)


if __name__ == "__main__":
    _demo_csv_meta_cache()
