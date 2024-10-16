import { Input, TagsInput } from "@mantine/core";
import { VariableSetter } from "../types";

export function Hallele({ value, setValue }: VariableSetter<string[]>) {
  return (
    <Input.Wrapper
      label="Peptide Length"
      description="Enter a number and press enter."
    >
      <TagsInput
        value={value}
        onChange={(v) => {
          if (v.length === 0) {
            setValue(v);
            return;
          }

          // Check the value can be converted to integer
          const newValue = Number(value[value.length - 1]);
          if (Number.isInteger(newValue)) {
            setValue(v);
          }
        }}
      />
    </Input.Wrapper>
  );
}
