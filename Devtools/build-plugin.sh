# this scripts builds the EAPM plugin into .hp format

# Enter the Plugin directory
cd Immunoinformatics

# Zip the files
zip -r Immunoinformatics.hp *

# Move the zip file to the root directory
mv Immunoinformatics.hp ../