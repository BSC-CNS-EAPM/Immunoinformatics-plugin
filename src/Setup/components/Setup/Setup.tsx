import { Button, Divider, Group, Stack, Stepper } from "@mantine/core";
import { useEffect, useState } from "react";

import { PREDIG_MODELS, SelectModel } from "./FormComponents/Select.Model";
import { ConfigurationSavedModal } from "./FormComponents/Save.Variable";
import { PredIGVariables, SimulationMode } from "./types";
import { CSVInput } from "./FormComponents/CSV.Input";
import { SelectSimulation } from "./FormComponents/Select.Simulation";
import { Hallele } from "./FormComponents/Hallele";

const DEFAULT_SETUP: PredIGVariables = {
  simulation: SimulationMode.UNIPROT,
  input_text: "",
  seed: Math.floor(Math.random() * 10000),
  modelXG: PREDIG_MODELS[0],
  HLA_alleles: "",
  peptide_len: ["8"],
  mat: "",
  alpha: 0.5,
  precursor_len: 9,
};

export function Setup() {
  const [predIGVariables, setPredIGVariables] = useState(DEFAULT_SETUP);

  // Stepper
  const [active, setActive] = useState(0);
  const nextStep = () =>
    setActive((current) => (current < 4 ? current + 1 : current));
  const prevStep = () =>
    setActive((current) => (current > 0 ? current - 1 : current));

  useEffect(() => {
    // For the first open, load the inputs from the variable
    if (parent?.horus?.getVariable) {
      const variable = parent.horus?.getVariable();

      if (variable?.value) {
        setPredIGVariables(variable.value);
      }
    }
  }, []);

  useEffect(() => {
    if (parent?.horus?.setVariable) {
      parent.horus?.setVariable(predIGVariables);
    }
  }, [predIGVariables]);

  return (
    <Stack m="lg" gap="lg">
      <Divider />
      <Stepper active={active} onStepClick={setActive}>
        <Stepper.Step label="Exploration mode" />
        <Stepper.Step label="Upload input" />
        <Stepper.Step label="Simulation setup" />

        <Stepper.Step label="Submit simulation" />
      </Stepper>
      <Divider />
      <StepViewer
        step={active}
        predIGVariables={predIGVariables}
        setPredIGVariables={setPredIGVariables}
      />

      <Divider />
      <Group justify="center" mt="xl">
        {active !== 0 && (
          <Button variant="default" onClick={prevStep}>
            Back
          </Button>
        )}
        {active !== 3 && <Button onClick={nextStep}>Next step</Button>}
      </Group>
    </Stack>
  );
}

function StepViewer({
  step,
  predIGVariables,
  setPredIGVariables,
}: {
  step: number;
  predIGVariables: PredIGVariables;
  setPredIGVariables: (predIGVariables: PredIGVariables) => void;
}) {
  switch (step) {
    case 0:
      return (
        <SelectSimulation
          predIGVariables={predIGVariables}
          setPredIGVariables={setPredIGVariables}
        />
      );
    case 1:
      return (
        <CSVInput
          file={
            predIGVariables.simulation === SimulationMode.FASTA
              ? "FASTA file"
              : "CSV/TSV file"
          }
          label={
            predIGVariables.simulation === SimulationMode.FASTA
              ? "FASTA file"
              : "CSV/TSV file"
          }
          description={
            predIGVariables.simulation === SimulationMode.FASTA
              ? undefined
              : "The input must have the following columns: peptide, allele, uniprot_id"
          }
          value={predIGVariables.input_text}
          setValue={(input_text) =>
            setPredIGVariables({ ...predIGVariables, input_text })
          }
        />
      );
    case 2:
      return (
        <>
          <SelectModel
            label="Select prediction model"
            value={predIGVariables.modelXG}
            setValue={(modelXG) =>
              setPredIGVariables({ ...predIGVariables, modelXG })
            }
          />
          {predIGVariables.simulation === SimulationMode.FASTA && (
            <Hallele
              label="Select HLA alleles"
              value={predIGVariables.HLA_alleles}
              setValue={(HLA_alleles) =>
                setPredIGVariables({ ...predIGVariables, HLA_alleles })
              }
            />
          )}
        </>
      );
    case 3:
      return <ConfigurationSavedModal />;
    default:
      return (
        <SelectSimulation
          predIGVariables={predIGVariables}
          setPredIGVariables={setPredIGVariables}
        />
      );
  }
}
