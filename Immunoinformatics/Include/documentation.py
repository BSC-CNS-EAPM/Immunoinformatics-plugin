from HorusAPI import PluginEndpoint, PluginPage

# Define the Documentation PredIG page
documentationViewPage = PluginPage(
    id="documentationView",
    name="PredIG documentation view",
    description="View the PredIG documentation",
    html="index.html",  # The HTML file to load
)
