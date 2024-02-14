"""
Entry point for the Immunoinformatics plugin
"""

from HorusAPI import Plugin


def createPlugin():
    """
    Generates the Immunoinformatics plugin and returns the instance
    """
    # ========== Plugin Definition ========== #

    ImmunoPlugin = Plugin(id="Immuno",)

    # ========== Blocks ========== #
    #from Blocks.AlphaFoldEAPM import alphafoldBlock  # type: ignore

    # Add the block to the plugin
    #frescoPlugin.addBlock(alphafoldBlock)



    # Return the plugin
    return ImmunoPlugin


plugin = createPlugin()
