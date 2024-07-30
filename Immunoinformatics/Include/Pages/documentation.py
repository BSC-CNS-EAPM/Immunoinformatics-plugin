from HorusAPI import PluginPage

# Define the Documentation PredIG page
documentationViewPage = PluginPage(
    id="documentationView",
    name="PredIG documentation view",
    description="View the PredIG documentation",
    html="load_pdf.html",  # The HTML file to load
)
