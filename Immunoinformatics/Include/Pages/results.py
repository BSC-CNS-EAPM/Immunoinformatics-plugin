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
        return Response("CSV does not exist", status=400)

    import pandas as pd

    df = pd.read_csv(full_csv)

    data_dict = df.to_dict(orient="records")

    return jsonify({"ok": True, "results": data_dict, "columns": list(df.columns)})


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
        zip_name = folder_name + ".zip"
        full_zip_path = os.path.join(os.path.dirname(folder_to_download), folder_name)

        # Compress the folder
        if os.path.exists(full_zip_path):
            os.remove(full_zip_path)

        import shutil

        os.chdir(folder_to_download)
        shutil.make_archive(
            full_zip_path,
            "zip",
            root_dir=folder_to_download,
        )

        download_name = name + ".zip" if name else None

        @after_this_request
        def remove_file(response):
            if os.path.exists(full_zip_path):
                os.remove(full_zip_path)

    else:
        # Download the csv
        full_zip_path = full_csv
        download_name = name + ".csv" if name else None

    return send_file(full_zip_path, as_attachment=True, download_name=download_name)


download_results_endpoint = PluginEndpoint(
    url="/results_api/download_results/", methods=["GET"], function=download_results
)


results_page.addEndpoint(download_results_endpoint)
