"""
Entry point for the Immunoinformatics plugin
"""

from HorusAPI import Plugin


def createPlugin():
    """
    Generates the Immunoinformatics plugin and returns the instance
    """
    # ========== Plugin Definition ========== #

    immunoPlugin = Plugin(id="Immuno",)

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



    # Return the plugin
    return immunoPlugin


plugin = createPlugin()
