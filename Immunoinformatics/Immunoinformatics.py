"""
Entry point for the Immunoinformatics plugin
"""

from HorusAPI import Plugin


def create_plugin():
    """
    Generates the Immunoinformatics plugin and returns the instance
    """
    # ========== Plugin Definition ========== #

    immunoPlugin = Plugin()

    # ========== Blocks ========== #
    from Blocks.PredIG import predigBlock  # type: ignore

    immunoPlugin.addBlock(predigBlock)

    from Blocks.NOAH import noahBlock  # type: ignore

    immunoPlugin.addBlock(noahBlock)

    from Blocks.NetCleave import netCleaveBlock  # type: ignore

    immunoPlugin.addBlock(netCleaveBlock)

    from Blocks.Documentation import documentationBlock  # type: ignore

    immunoPlugin.addBlock(documentationBlock)

    from Blocks.PredIGmodels import predig_modelsBlock  # type: ignore

    immunoPlugin.addBlock(predig_modelsBlock)

    from Blocks.Tap import tapBlock  # type: ignore

    immunoPlugin.addBlock(tapBlock)

    # ========== Configs ========== #
    from Configs.columns_to_delete import columns_to_delete_config

    immunoPlugin.addConfig(columns_to_delete_config)

    from Configs.python_exec import python_exec_config

    immunoPlugin.addConfig(python_exec_config)

    from Configs.noahConfig import noahExecutableConfig

    immunoPlugin.addConfig(noahExecutableConfig)

    from Configs.netCleaveConfig import netClaveExecutableConfig

    immunoPlugin.addConfig(netClaveExecutableConfig)

    from Configs.pchConfig import pchExecutableConfig

    immunoPlugin.addConfig(pchExecutableConfig)

    from Configs.mhcflurryConfig import mhcflurryExecutableConfig

    immunoPlugin.addConfig(mhcflurryExecutableConfig)

    from Configs.tapmapConfig import tapmatExecutableConfig

    immunoPlugin.addConfig(tapmatExecutableConfig)

    # ========== Pages ========== #
    from Pages.documentation import documentationViewPage

    immunoPlugin.addPage(documentationViewPage)

    from Pages.setup_predig import setup_predig_page

    immunoPlugin.addPage(setup_predig_page)

    from Pages.results import results_page

    immunoPlugin.addPage(results_page)

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
