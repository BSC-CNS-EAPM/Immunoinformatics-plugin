import subprocess

from HorusAPI import PluginConfig, PluginVariable, VariableTypes

predigPCHPathVariable = PluginVariable(
    id="PCH_path",
    name="PCH path",
    description="Path to the PCH executable",
    type=VariableTypes.FILE,
    defaultValue="predig_pch_calc.R",
)
predigMHCflurryPathVariable = PluginVariable(
    id="MHC_path",
    name="MHCflurry path",
    description="Path to the MHCflurry executable",
    type=VariableTypes.FILE,
    defaultValue="mhcflurry-predict",
)


def checkInstallations(block: PluginConfig):
    import os

    print("verifying PCH installation")

    # Get the path to the noah executable
    predigPCH = block.variables.get("PCH_path")
    # Get the path to the noah parser executable
    predigMHCflurry = block.variables.get("MHC_path")

    # Check if the path is valid
    if not os.path.isfile(predigPCH):
        raise Exception("The PCH executable path is not valid")

    print("verifying MHCflurry installation")
    # Check if the path is valid
    if str(predigMHCflurry).startswith("mhcflurry"):
        try:
            # Run the command and get the output
            output = subprocess.check_output(
                "mhcflurry-predict -h", shell=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            # If the command fails, it will raise a CalledProcessError
            if "command not found" in str(e.output):
                raise Exception("mhcflurry-predict command not found")
    elif not os.path.isfile(predigMHCflurry):
        raise Exception("The MHCflurry parser executable path is not valid")


# Create a plugin configuration for the PredIG executables
predigExecutableConfig = PluginConfig(
    name="PredIGs executables",
    description="Configure the path to the PredIGs executables.",
    variables=[predigPCHPathVariable, predigMHCflurryPathVariable],
    action=checkInstallations,
)
