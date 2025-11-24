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
  mat: "",
  alpha: 0.5,
  precursor_len: 9,
};

const SAMPLE_DATA = {
  [SimulationMode.UNIPROT]: "predig_input1_uniprot_example.csv",
  [SimulationMode.RECOMBINANT]: "predig_input2_recombinant_example.csv",
  [SimulationMode.FASTA]: "predig_input3_b2m_fasta_example.fasta",
  alleles: "predig_input3_alleles_example.csv",
};

const getEnumKeyByValue = (value: string, enumObj: any) => {
  return Object.keys(enumObj).find((key) => enumObj[key] === value);
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
    if (window?.horusVariable?.getVariable) {
      const variable = window.horusVariable?.getVariable();

      if (variable?.value) {
        setPredIGVariables(variable.value);
      }
    }
  }, []);

  useEffect(() => {
    if (window?.horusVariable?.setVariable) {
      window.horusVariable?.setVariable(predIGVariables);
    }
  }, [predIGVariables]);

  return (
    <Stack m="lg" gap="lg">
      <Divider />
      <Stepper active={active} onStepClick={setActive}>
        <Stepper.Step
          label="Exploration mode"
          description={getEnumKeyByValue(
            predIGVariables.simulation,
            SimulationMode
          )}
        />
        <Stepper.Step
          label="Upload input"
          description={
            predIGVariables.input_text ? "Uploaded" : "Upload a file"
          }
        />
        <Stepper.Step
          label="Simulation setup"
          description={predIGVariables.modelXG}
        />

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

const UNIPROT_COLUMNS = "epitope,HLA_allele,uniprot_id";
const RECOMBINANT_COLUMNS = "epitope,HLA_allele,protein_seq,protein_name";

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
          setPredIGVariables={(v) => {
            setPredIGVariables({ ...v, input_text: "" });
          }}
        />
      );
    case 1:
      return (
        <CSVInput
          sampleData={SAMPLE_DATA[predIGVariables.simulation]}
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
              ? "Upload a FASTA file"
              : `The input CSV must have the following columns: ${predIGVariables.simulation === SimulationMode.RECOMBINANT ? RECOMBINANT_COLUMNS : UNIPROT_COLUMNS}`
          }
          validator={(value) => {
            if (predIGVariables.simulation === SimulationMode.RECOMBINANT) {
              // The first line of recombinant must be epitope, HLA_allele, protein_seq
              if (value.split("\n")[0] !== RECOMBINANT_COLUMNS) {
                return `The first line must be '${RECOMBINANT_COLUMNS}'`;
              }

              // For the rest of rows, check the number of columns
              const lines = value.split("\n");
              for (let i = 1; i < lines.length; i++) {
                const line = lines[i];
                if (
                  line.split(",").length !==
                  RECOMBINANT_COLUMNS.split(",").length
                ) {
                  return `Line ${i + 1} must have ${RECOMBINANT_COLUMNS.split(",").length} columns`;
                }
              }
            }

            if (predIGVariables.simulation === SimulationMode.UNIPROT) {
              // The first line of recombinant must be peptide,allele,uniprot_id
              if (value.split("\n")[0] !== UNIPROT_COLUMNS) {
                return `The first line must be '${UNIPROT_COLUMNS}'`;
              }

              // For the rest of rows, they have to be at least 3 columns
              const lines = value.split("\n");
              for (let i = 1; i < lines.length; i++) {
                const line = lines[i];
                if (
                  line.split(",").length !== UNIPROT_COLUMNS.split(",").length
                ) {
                  return `Line ${i + 1} must have ${UNIPROT_COLUMNS.split(",").length} columns`;
                }
              }
            }

            return false;
          }}
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
              sampleData={SAMPLE_DATA["alleles"]}
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
