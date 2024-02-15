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

    # Add the block to the plugin
    immunoPlugin.addBlock(predigBlock)


    # Return the plugin
    return immunoPlugin


plugin = createPlugin()
