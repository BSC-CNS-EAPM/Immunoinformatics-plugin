declare global {
  interface Window {
    horus: any;
  }
}

export enum SimulationMode {
  FASTA = "1",
  UNIPROT = "2",
  RECOMBINANT = "3",
}

export type PredIGVariables = {
  simulation: SimulationMode;
  input_text: string;
  seed: number;
  modelXG: string;
  HLA_alleles: string;
  peptide_len?: string[];
  mat: string;
  alpha: number;
  precursor_len: number;
};

export type VariableSetter<T> = {
  validator?: (value: T) => string | boolean;
  label: string;
  description?: string;
  value: T;
  file?: string;
  setValue: (newValue: T) => void;
  sampleData?: T;
};

export type SimulationModeProps = {
  predIGVariables: PredIGVariables;
  setPredIGVariables: (predIGVariables: PredIGVariables) => void;
};
