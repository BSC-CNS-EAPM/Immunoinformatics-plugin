from HorusAPI import PluginPage

# Define the Setup PredIG page
setup_predig_page = PluginPage(
    id="immuno",
    name="Setup PredIG",
    description="Setup the PredIG simulation",
    html="index.html",  # The HTML file to load
    hidden=True,
)
