import os
from HorusAPI import PluginPage, PluginEndpoint
import typing

results_page = PluginPage(
    id="results",
    name="Results",
    description="View the results of a block",
    html="results.html",  # The HTML file to load
    hidden=True,
)


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

    try:
        df = pd.read_csv(full_csv)

        # Replace all NAN values with None
        df = df.replace({np.nan: None})

        data_dict = df.to_dict(orient="records")

        return jsonify({"ok": True, "results": data_dict, "columns": list(df.columns)})

    except Exception as e:
        return Response(str(e), status=400)


results_data_endpoint = PluginEndpoint(
    url="/results_api/results/", methods=["GET"], function=return_data
)

results_page.addEndpoint(results_data_endpoint)


def zip_folder(folder: str, destination: str, skip_folders: bool) -> None:
    """
    Compress `folder` into the `destination` zip file.

    `skip_folders` keeps only the files sitting directly in the folder and
    leaves its subfolders out. That is what makes the archive downloadable for
    a TCoaRse run: the tables, the pyDock archive and the status file are a few
    megabytes, while the intermediates next to them ('<prefix>_pdb' and
    '<prefix>_cm', one file per model) can run to gigabytes.
    """
    import zipfile

    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, folders, files in os.walk(folder):
            if skip_folders:
                # Emptied in place, which is how os.walk is told not to descend
                folders[:] = []

            for file in files:
                path = os.path.join(root, file)
                archive.write(path, os.path.relpath(path, folder))


def download_results():
    from flask import request, Response, send_file, after_this_request

    data: dict = request.args

    csv: typing.Union[str, None] = data.get("csv")
    simulation: typing.Union[str, None] = data.get("simulation")
    skip_folders: typing.Union[str, None] = data.get("skip_folders")
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

    download_name: typing.Union[str, None] = None
    if simulation:
        folder_to_download = os.path.dirname(full_csv)
        folder_name = os.path.basename(folder_to_download)

        import shutil
        import tempfile

        # Built in a temporary folder rather than next to the results one: the
        # run folder stays as the flow left it, and two downloads of the same
        # flow cannot overwrite each other's archive halfway through
        temp_dir = tempfile.mkdtemp()
        full_zip_path = os.path.join(temp_dir, folder_name + ".zip")

        zip_folder(folder_to_download, full_zip_path, bool(skip_folders))

        download_name = name + ".zip" if name else None

        @after_this_request
        def remove_file(response):
            shutil.rmtree(temp_dir, ignore_errors=True)
            return response

    else:
        # Download the csv
        full_zip_path = full_csv
        download_name = name + ".csv" if name else None

    return send_file(full_zip_path, as_attachment=True, download_name=download_name)


download_results_endpoint = PluginEndpoint(
    url="/results_api/download_results/", methods=["GET"], function=download_results
)


results_page.addEndpoint(download_results_endpoint)
