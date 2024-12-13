import { Input, Text, Textarea } from "@mantine/core";
import { VariableSetter } from "../types";
import { CSVInput } from "./CSV.Input";
import { useState } from "react";

export function Hallele({
  value,
  setValue,
  sampleData,
}: VariableSetter<string>) {
  const halleleValidator = (value: string | undefined) => {
    if (!value) {
      return false;
    }

    const lines = value.split("\n");

    if (lines.length === 0) {
      return false;
    }

    for (const line of lines) {
      // If the line is empty skip
      if (line.trim() === "") {
        continue;
      }

      if (!line.match(/^HLA-[ABC]\*[0-9]{1,3}:[0-9]{1,3}$/)) {
        return false;
      }
    }

    return true;
  };

  return (
    <Input.Wrapper>
      <CSVInput
        sampleData={sampleData}
        label="HLA Alleles"
        file="TXT File"
        value={value}
        setValue={setValue}
        validator={(value) => {
          return halleleValidator(value)
            ? false
            : "Please modify or remove the alleles in your list that are not part of the HLA 4-digits resolution format established by IMGT. e.g HLA-A*02:01 or HLA-A*100:101.";
        }}
        description="Provide a list of HLA Alleles in the format 'HLA-A*02:01'"
      />
    </Input.Wrapper>
  );
}
