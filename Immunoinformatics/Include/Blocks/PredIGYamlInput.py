"""
Module containing an InputBlock to write the PredIG YAML setup directly in an editor
"""

import os

from HorusAPI import InputBlock, PluginBlock, PluginVariable, VariableTypes

with open(
    os.path.join(
        os.path.dirname(__file__), "..", "examples", "predig_setup_example.yaml"
    ),
    encoding="utf-8",
) as _f:
    _default_yaml = _f.read()

yaml_code_variable = PluginVariable(
    id="predig_yaml_code",
    name="PredIG YAML",
    description="Write the PredIG setup YAML directly, as an alternative to uploading a file. Wire the output into PredIG's 'Input YAML'.",
    type=VariableTypes.CODE,
    allowedValues=["yaml"],
    defaultValue=_default_yaml,
)

output_yaml_variable = PluginVariable(
    id="predig_yaml_file",
    name="PredIG YAML file",
    description="The YAML file written from the editor.",
    type=VariableTypes.FILE,
    allowedValues=["yaml"],
)


def write_predig_yaml(block: PluginBlock):
    """
    Write the edited YAML code to a file and output its path
    """
    yaml_code = block.variables.get(yaml_code_variable.id, "")
    filename = "predig_setup.yaml"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(yaml_code)
    block.setOutput(output_yaml_variable.id, filename)


predigYamlInputBlock = InputBlock(
    name="PredIG YAML Input",
    description="Write the PredIG setup YAML directly in an editor and output it as a file, to wire into PredIG's 'Input YAML'.",
    variable=yaml_code_variable,
    output=output_yaml_variable,
    action=write_predig_yaml,
)
