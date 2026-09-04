import os
import typing

from HorusAPI import PluginEndpoint, PluginPage
from pydantic import BaseModel, ValidationError, field_validator

results_page = PluginPage(
    id="results",
    name="PredIG results",
    description="View the PredIG results",
    html="results.html",  # The HTML file to load
    hidden=True,
)


class CsvMeta(BaseModel):
    """Cached column names / row count for a csv, sidecar-persisted next to it."""

    mtime: float
    size: int
    columns: list[str]
    total_rows: int


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 100

    @field_validator("page", mode="before")
    @classmethod
    def _clamp_page(cls, v):
        try:
            return max(1, int(v))
        except (TypeError, ValueError):
            return 1

    @field_validator("page_size", mode="before")
    @classmethod
    def _clamp_page_size(cls, v):
        try:
            return max(1, min(10000, int(v)))
        except (TypeError, ValueError):
            return 100


class ResultsResponse(BaseModel):
    ok: bool = True
    results: list[dict]
    columns: list[str]
    total: int
    page: int
    page_size: int
    total_pages: int


def _csv_meta_cache_path(full_csv: str) -> str:
    return full_csv + ".pagemeta.json"


def _load_csv_meta(full_csv: str, stat: "os.stat_result") -> typing.Optional[CsvMeta]:
    """
    Read the cached columns/row count for full_csv if a sidecar cache file
    exists and still matches the file's mtime/size, else None.

    Each request runs in its own forked subprocess (Server.PluginManager
    SubprocessManager.subprocessCall), so an in-memory cache would not
    survive between requests; the cache is persisted to disk instead.
    """

    cache_path = _csv_meta_cache_path(full_csv)
    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, "r") as f:
            meta = CsvMeta.model_validate_json(f.read())
    except (OSError, ValidationError):
        return None

    if meta.mtime != stat.st_mtime or meta.size != stat.st_size:
        return None

    return meta


def _save_csv_meta(full_csv: str, meta: CsvMeta) -> None:
    try:
        with open(_csv_meta_cache_path(full_csv), "w") as f:
            f.write(meta.model_dump_json())
    except OSError:
        pass


def return_data():

    from flask import Response, jsonify, request

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

    import math

    import numpy as np
    import pandas as pd

    try:
        stat = os.stat(full_csv)
        meta = _load_csv_meta(full_csv, stat)
        if meta is None:
            # Read header only to get column names
            columns = list(pd.read_csv(full_csv, nrows=0).columns)

            # Count total rows efficiently without loading entire file into memory
            with open(full_csv, "rb") as f:
                total_rows = max(0, sum(1 for line in f if line.strip()) - 1)

            meta = CsvMeta(
                mtime=stat.st_mtime,
                size=stat.st_size,
                columns=columns,
                total_rows=total_rows,
            )
            _save_csv_meta(full_csv, meta)

        pagination = PaginationParams(
            page=data.get("page", 1),
            page_size=data.get("page_size", data.get("limit", 100)),
        )

        total_pages = (
            math.ceil(meta.total_rows / pagination.page_size)
            if meta.total_rows > 0
            else 1
        )
        skip_count = (pagination.page - 1) * pagination.page_size

        if meta.total_rows == 0 or skip_count >= meta.total_rows:
            data_dict = []
        else:
            df = pd.read_csv(
                full_csv,
                skiprows=range(1, skip_count + 1),
                nrows=pagination.page_size,
            )
            # Replace all NaN values with None
            df = df.replace({np.nan: None})
            data_dict = df.to_dict(orient="records")

        response = ResultsResponse(
            results=data_dict,
            columns=meta.columns,
            total=meta.total_rows,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
        )

        return jsonify(response.model_dump())

    except Exception as e:
        return Response(str(e), status=400)


results_data_endpoint = PluginEndpoint(
    url="/results_api/results/", methods=["GET"], function=return_data
)

results_page.addEndpoint(results_data_endpoint)


def download_results():
    from flask import Response, after_this_request, request, send_file

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
