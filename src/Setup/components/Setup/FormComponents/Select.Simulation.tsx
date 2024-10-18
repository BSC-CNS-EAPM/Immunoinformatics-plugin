import { Radio, Group, Text, Grid } from "@mantine/core";
import classes from "./Select.Simulation.module.css";
import { SimulationMode, SimulationModeProps } from "../types";

const data = [
  {
    value: SimulationMode.UNIPROT,
    name: "Uniprot",
    description:
      "Input a .CSV file with pairs of peptide and HLA-I allele and the Uniprot ID of the corresponding parental protein.",
  },
  {
    value: SimulationMode.RECOMBINANT,
    name: "Recombinant",
    description:
      "Input a .CSV file with pairs of peptide and HLA-I allele and the amino acid sequence of the protein of origin. This mode is designed to support (recombinant) proteins without Uniprot ID but can also work with any protein sequence.",
  },
  {
    value: SimulationMode.FASTA,
    name: "FASTA",
    description:
      "Input a FASTA file with the target protein sequence and a .CSV file with a list of HLA-I alleles of interest ('HLA_allele' column). By default, PredIG will generate all possible epitopes of 8 to 14 AA of length and will calculate against the input HLA-I alleles.",
  },
];

export function SelectSimulation(props: SimulationModeProps) {
  const { predIGVariables, setPredIGVariables } = props;

  const cards = data.map((item) => (
    <Grid.Col span={4} key={item.name}>
      <Radio.Card
        className={classes.root}
        radius="md"
        value={item.value}
        key={item.name}
        h={"250px"}
      >
        <Group wrap="nowrap" align="flex-start" h={"100%"}>
          <Radio.Indicator />
          <div>
            <Text className={classes.label}>{item.name}</Text>
            <Text className={classes.description}>{item.description}</Text>
          </div>
        </Group>
      </Radio.Card>
    </Grid.Col>
  ));

  return (
    <Radio.Group
      value={predIGVariables.simulation}
      onChange={(e) => {
        console.log("changed", e);
        setPredIGVariables({
          ...predIGVariables,
          simulation: e as SimulationMode,
        });
      }}
      label="Exploration Modes"
    >
      <Grid pt="md" grow gutter="xs">
        {cards}
      </Grid>
    </Radio.Group>
  );
}
