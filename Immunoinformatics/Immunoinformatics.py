"""
Entry point for the Immunoinformatics plugin
"""

from HorusAPI import Plugin


def create_plugin():
    """
    Generates the Immunoinformatics plugin and returns the instance
    """
    # ========== Plugin Definition ========== #

    immunoPlugin = Plugin(id="Immuno")

    # ========== Blocks ========== #
    from Blocks.PredIG import predigBlock  # type: ignore

    immunoPlugin.addBlock(predigBlock)

    from Blocks.NOAH import noahBlock  # type: ignore

    immunoPlugin.addBlock(noahBlock)

    from Blocks.NetCleave import netCleaveBlock  # type: ignore

    immunoPlugin.addBlock(netCleaveBlock)

    # Add the configs
    from Configs.noahConfig import noahExecutableConfig

    immunoPlugin.addConfig(noahExecutableConfig)

    from Configs.netCleaveConfig import netClaveExecutableConfig

    immunoPlugin.addConfig(netClaveExecutableConfig)

    from Configs.predIGConfig import predigExecutableConfig

    immunoPlugin.addConfig(predigExecutableConfig)

    # Return the plugin
    return immunoPlugin


plugin = create_plugin()

"""Dependencies:
    "scikit-learn",
    "pandas",
    "numpy",
    "matplotlib",
    "argparse",
    "pathlib",
    "keras",
    "tensorflow",
    "biopython",
    "pytz",
    "pip mhcflurry",
    "rpy2"
"""
