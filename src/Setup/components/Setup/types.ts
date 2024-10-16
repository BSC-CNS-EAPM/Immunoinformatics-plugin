declare global {
  interface Window {
    horus: any;
  }
}

export enum ModelTypes {
  PROVIDED = "provided",
  CUSTOM = "custom",
}

export type PredIGVariables = {
  input_text: string;
  seed: number;
  modelXG: string;
  predig_model_type: ModelTypes;
  HLA_allele: string;
  peptide_len: string[];
  mat: string;
  alpha: number;
  precursor_len: number;
};

export type VariableSetter<T> = {
  value: T;
  setValue: (newValue: T) => void;
};
