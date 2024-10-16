import { Stack } from "@mantine/core";
import { useEffect, useState } from "react";

import { CSVInput } from "./FormComponents/CSV.Input";
import { PREDIG_MODELS, SelectModel } from "./FormComponents/Select.Model";
import { ConfigurationSavedModal } from "./FormComponents/Save.Variable";
import { ModelTypes, PredIGVariables } from "./types";

const DEFAULT_SETUP: PredIGVariables = {
  input_text: "",
  seed: Math.floor(Math.random() * 10000),
  predig_model_type: ModelTypes.PROVIDED,
  modelXG: PREDIG_MODELS[0],
  HLA_allele: "",
  peptide_len: ["8"],
  mat: "",
  alpha: 0.5,
  precursor_len: 9,
};

export function Setup() {
  const [prediIGVariables, setPrediIGVariables] = useState(DEFAULT_SETUP);

  useEffect(() => {
    // For the first open, load the inputs from the variable
    const variable = parent.horus.getVariable();

    if (variable?.value) {
      setPrediIGVariables(variable.value);
    }
  }, []);

  return (
    <Stack m="lg" gap="lg">
      <CSVInput
        value={prediIGVariables.input_text}
        setValue={(input_text) =>
          setPrediIGVariables({ ...prediIGVariables, input_text })
        }
      />
      <SelectModel
        value={prediIGVariables.modelXG}
        setValue={(modelXG) =>
          setPrediIGVariables({ ...prediIGVariables, modelXG })
        }
      />

      <ConfigurationSavedModal predIGVariables={prediIGVariables} />
    </Stack>
  );
}
