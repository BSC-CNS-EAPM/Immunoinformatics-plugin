import { Input } from "@mantine/core";
import { VariableSetter } from "../types";

export function Hallele({ value, setValue }: VariableSetter<number>) {
  return (
    <Input.Wrapper label="Precursor Length">
      <Input
        value={value}
        placeholder="9"
        onChange={(e) => {
          if (Number.isInteger(Number(e.target.value))) {
            setValue(Number(e.target.value));
          }
        }}
      />
    </Input.Wrapper>
  );
}
