
#!/bin/bash

echo "Building plugin..."

# Clean

npm run clean

rm Immunoinformatics*.hp

# Ask for the plugin version
read -p "Plugin version: " version

# Build the Pages

npm run build

# Update the plugin.json with the version
# If we are on macOS, use gsed, otherwise sed
if [ "$(uname)" = "Darwin" ]; then
    SED_COMMAND="gsed"
else
    SED_COMMAND="sed"
fi

# Update the version
$SED_COMMAND -i -e "s/\"version\": \"[0-9]*\.[0-9]*\.[0-9]*\"/\"version\": \"$version\"/g" Immunoinformatics/plugin.meta

# Create the zip

zip -r Immunoinformatics-$version.hp Immunoinformatics

# Restore the version back to 0.0.0

$SED_COMMAND -i -e "s/\"version\": \"$version\"/\"version\": \"0.0.0\"/g" Immunoinformatics/plugin.meta
