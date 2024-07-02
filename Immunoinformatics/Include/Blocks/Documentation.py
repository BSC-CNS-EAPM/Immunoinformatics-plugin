"""
Module containing the NetCleave block for the Immunoinformatics plugin 
"""

from HorusAPI import Extensions, PluginBlock

# ==========================#
# Variable inputs
# ==========================#


# ==========================#
# Variable outputs
# ==========================#


def show_documentation(block: PluginBlock):
    Extensions().storeExtensionResults(
        pluginID="immuno", pageID="documentationview", title="PredIG Documentation"
    )


# ==========================#
# Block definition
# ==========================#
documentationBlock = PluginBlock(
    name="PredIG documentation",
    description="The documentation for the PredIG block.",
    inputs=[],
    outputs=[],
    variables=[],
    action=show_documentation,
)
