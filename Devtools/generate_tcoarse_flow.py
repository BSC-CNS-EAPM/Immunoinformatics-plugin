"""
Generate the TCoaRse flow preset (Immunoinformatics/Flows/TCoaRse.flow).

The preset wires the 15 TCoaRse blocks the same way tcoarse_prediction.nf wires
its processes. It is generated from the block definitions themselves so that it
never drifts from the ids declared in Include/Blocks/TCoaRse.

Usage (needs a python with HorusAPI importable, e.g. the `horus` env):

    python Devtools/generate_tcoarse_flow.py [--horus /path/to/horus/checkout]
"""

import argparse
import datetime
import hashlib
import json
import os
import sys
import zipfile

PLUGIN_ID = "immuno"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUDE_DIR = os.path.join(REPO_ROOT, "Immunoinformatics", "Include")
FLOW_PATH = os.path.join(REPO_ROOT, "Immunoinformatics", "Flows", "TCoaRse.flow")

FLOW_NAME = "TCoaRse"

# module -> (block variable, x, y)
LAYOUT = [
    ("AF3Outputs", "af3OutputsBlock", -320.0, 120.0),
    ("QualityMetrics", "qualityMetricsBlock", 40.0, -240.0),
    ("QualityTier", "qualityTierBlock", 400.0, -240.0),
    ("CopyModels", "copyModelsBlock", 40.0, 200.0),
    ("StructureMetadata", "structureMetadataBlock", 400.0, 200.0),
    ("Similarities", "similaritiesBlock", 760.0, 40.0),
    ("Embeddings", "embeddingsBlock", 760.0, 280.0),
    ("PredictorESMC", "predictorESMCBlock", 1120.0, 280.0),
    ("PyDockEnergies", "pydockEnergiesBlock", 400.0, 520.0),
    ("ContactMaps", "contactMapsBlock", 400.0, 720.0),
    ("PairwiseDockQ", "pairwiseDockQBlock", 400.0, 920.0),
    ("EnergeticScorer", "energeticScorerBlock", 760.0, 720.0),
    ("MergeEnergies", "mergeEnergiesBlock", 1120.0, 580.0),
    ("PredictorTCoaRse", "predictorTCoaRseBlock", 1480.0, 500.0),
    ("PredictorBimodal", "predictorBimodalBlock", 1480.0, 720.0),
]

# (origin module, output id, destination module, input id)
CONNECTIONS = [
    ("AF3Outputs", "af3_dir", "QualityMetrics", "af3_dir"),
    ("AF3Outputs", "af3_dir", "CopyModels", "af3_dir"),
    ("QualityMetrics", "metrics_csv", "QualityTier", "metrics_csv"),
    ("CopyModels", "pdb_dir", "StructureMetadata", "pdb_dir"),
    ("CopyModels", "pdb_dir", "Similarities", "pdb_dir"),
    ("CopyModels", "pdb_dir", "PyDockEnergies", "pdb_dir"),
    ("CopyModels", "pdb_dir", "ContactMaps", "pdb_dir"),
    ("CopyModels", "pdb_dir", "PairwiseDockQ", "pdb_dir"),
    ("CopyModels", "pdb_dir", "EnergeticScorer", "pdb_dir"),
    ("StructureMetadata", "metadata_csv", "Similarities", "metadata_csv"),
    ("StructureMetadata", "metadata_csv", "Embeddings", "metadata_csv"),
    ("StructureMetadata", "metadata_csv", "PredictorESMC", "metadata_csv"),
    ("StructureMetadata", "metadata_csv", "MergeEnergies", "metadata_csv"),
    ("Embeddings", "embeddings_h5", "PredictorESMC", "embeddings_h5"),
    ("Embeddings", "embeddings_h5", "PredictorBimodal", "embeddings_h5"),
    ("ContactMaps", "cm_dir", "EnergeticScorer", "cm_dir"),
    ("EnergeticScorer", "energies_csv", "MergeEnergies", "energies_csv"),
    ("PyDockEnergies", "pydock_tar", "MergeEnergies", "pydock_tar"),
    ("MergeEnergies", "merged_csv", "PredictorTCoaRse", "merged_csv"),
    ("MergeEnergies", "merged_csv", "PredictorBimodal", "merged_csv"),
]


def _type_value(raw):
    """
    The flow file stores the plain value of the VariableTypes enum.
    """
    if isinstance(raw, str) and raw.startswith("VariableTypes."):
        from HorusAPI import VariableTypes

        return VariableTypes[raw.split(".", 1)[1]].value

    return raw


def _clean_types(node):
    """
    Recursively normalize every "type" entry of a serialized variable.
    """
    if isinstance(node, dict):
        return {
            key: (_type_value(value) if key == "type" else _clean_types(value))
            for key, value in node.items()
        }

    if isinstance(node, list):
        return [_clean_types(item) for item in node]

    return node


def _variable_info(variables, variable_id):
    """
    Find a serialized variable by id, looking inside input groups too.
    """
    for variable in variables:
        if variable.get("id") == variable_id:
            return variable

        for nested in variable.get("variables", []) or []:
            if nested.get("id") == variable_id:
                return nested

    raise KeyError(variable_id)


def build_flow(blocks):
    """
    Build the flow.json contents out of the block definitions.
    """

    placed_ids = {name: index + 1 for index, (name, _, _, _) in enumerate(LAYOUT)}

    serialized = {}
    for name, _, x, y in LAYOUT:
        block = blocks[name]
        serialized[name] = {
            "id": f"{PLUGIN_ID}.{block.id}".lower(),
            "isPlaced": True,
            "position": {"x": x, "y": y},
            "isRunning": False,
            "error": False,
            "blockLogs": "",
            "placedID": placed_ids[name],
            "finishedExecution": False,
            "outputs": _clean_types(block._variablesToDict(block._outputs)),
            "variables": _clean_types(block._variablesToDict(block._variables)),
            "variableConnections": [],
            "variableConnectionsReference": [],
            "selectedInputGroup": "default",
            "selectedRemote": "Local",
            "extensionsToOpen": [],
            "time": 0,
            "extraData": {},
            "dirty": False,
            "category": block.category,
            "color": block.color,
            "externalURL": block.externalURL,
            "name": block.name,
            "description": block.description,
            "inputs": _clean_types(block._inputGroupsToDict(block._inputGroups)),
            "type": _type_value(str(block.TYPE)),
            "isCustom": False,
            "rawBlock": None,
        }

    for origin, output_id, destination, input_id in CONNECTIONS:
        origin_block = serialized[origin]
        destination_block = serialized[destination]

        origin_variable = _variable_info(origin_block["outputs"], output_id)
        destination_variable = _variable_info(destination_block["inputs"], input_id)

        connection = {
            "origin": {
                "placedID": placed_ids[origin],
                "blockID": origin_block["id"],
                "variableID": output_id,
                "variableType": origin_variable["type"],
                "variableAllowedValues": origin_variable.get("allowedValues"),
            },
            "destination": {
                "placedID": placed_ids[destination],
                "blockID": destination_block["id"],
                "variableID": input_id,
                "variableType": destination_variable["type"],
                "variableAllowedValues": destination_variable.get("allowedValues"),
            },
            "isCyclic": False,
            "cycles": 1,
            "currentCycle": 0,
        }

        origin_block["variableConnectionsReference"].append(connection)
        destination_block["variableConnections"].append(connection)

    return {
        "name": FLOW_NAME,
        "savedID": hashlib.md5(FLOW_NAME.encode("utf-8")).hexdigest(),
        "path": FLOW_PATH,
        "status": "IDLE",
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "size": 0.0,
        "startedTime": None,
        "finishedTime": None,
        "elapsed": 0,
        "isPreset": False,
        "currentExecuting": None,
        "blocks": [serialized[name] for name, _, _, _ in LAYOUT],
        "terminalOutput": [],
        "pendingActions": [],
        "pendingSmilesActions": [],
        "pendingExtensions": [],
        "panels": {
            "grid": {
                "root": {
                    "type": "branch",
                    "data": [
                        {
                            "type": "leaf",
                            "data": {
                                "views": ["blockRegistry"],
                                "activeView": "blockRegistry",
                                "id": "blockRegistry",
                                "locked": True,
                            },
                            "size": 300,
                        },
                        {
                            "type": "leaf",
                            "data": {
                                "views": ["flow"],
                                "activeView": "flow",
                                "id": "1",
                            },
                            "size": 1024,
                        },
                    ],
                    "size": 824,
                },
                "width": 1324,
                "height": 824,
                "orientation": "HORIZONTAL",
            },
            "panels": {
                "flow": {
                    "id": "flow",
                    "contentComponent": "flow",
                    "tabComponent": "flow",
                    "params": {"status": "UNSAVED"},
                    "title": FLOW_NAME,
                    "renderer": "always",
                },
                "blockRegistry": {
                    "id": "blockRegistry",
                    "contentComponent": "blockRegistry",
                    "tabComponent": "props.defaultTabComponent",
                    "title": "Block Registry",
                    "renderer": "always",
                    "minimumWidth": 300,
                    "maximumWidth": 300,
                },
            },
            "activeGroup": "1",
        },
        "extraData": {},
        "flowRunInfo": None,
        "flowError": "",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--horus",
        default=os.path.expanduser("~/GitHub/horus"),
        help="Path to the Horus checkout that provides HorusAPI",
    )
    parser.add_argument("--output", default=FLOW_PATH)
    args = parser.parse_args()

    sys.path.insert(0, args.horus)
    sys.path.insert(0, INCLUDE_DIR)

    import importlib

    blocks = {}
    for module_name, block_name, _, _ in LAYOUT:
        module = importlib.import_module(f"Blocks.TCoaRse.{module_name}")
        blocks[module_name] = getattr(module, block_name)

    flow = build_flow(blocks)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("flow.json", json.dumps(flow))

    print(f"Wrote {args.output} ({len(flow['blocks'])} blocks, {len(CONNECTIONS)} connections)")


if __name__ == "__main__":
    main()
