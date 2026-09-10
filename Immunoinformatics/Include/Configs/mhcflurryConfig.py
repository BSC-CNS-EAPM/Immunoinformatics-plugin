from HorusAPI import PluginConfig, PluginVariable, VariableTypes

mhcflurryPathVariable = PluginVariable(
    id="MHC_path",
    name="MHCflurry path",
    description="Path to the MHCflurry executable",
    type=VariableTypes.FILE,
    defaultValue="mhcflurry-predict",
)


def checkInstallation(block: PluginConfig):
    import os
    import subprocess

    print("verifying MHCflurry installation")

    predigMHCflurry = block.variables.get(mhcflurryPathVariable.id)
    # Check if the path is valid
    if str(predigMHCflurry).startswith("mhcflurry"):
        try:
            # Run the command and get the output
            output = subprocess.check_output(
                "mhcflurry-predict -h", shell=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            # If the command fails, it will raise a CalledProcessError
            # Warn instead of raising: an exception here aborts the save of
            # every config that comes after this one (see noahConfig).
            if "command not found" in str(e.output):
                print("Warning: the mhcflurry-predict command was not found.")
    elif predigMHCflurry is None or not os.path.isfile(predigMHCflurry):
        print("Warning: the MHCflurry parser executable path is not valid on this machine.")


# Create a plugin configuration for the noah executable
mhcflurryExecutableConfig = PluginConfig(
    name="MHCflurry executable",
    description="Configure the path to the MHCflurry executables",
    variables=[mhcflurryPathVariable],
    action=checkInstallation,
)
