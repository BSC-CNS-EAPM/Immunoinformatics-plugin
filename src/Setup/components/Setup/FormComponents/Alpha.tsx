import { Input } from "@mantine/core";
import { VariableSetter } from "../types";

export function Hallele({ value, setValue }: VariableSetter<number>) {
  return (
    <Input.Wrapper label="Alpha">
      <Input
        value={value}
        placeholder="0.5"
        onChange={(e) => {
          if (Number.isInteger(Number(e.target.value))) {
            setValue(Number(e.target.value));
          }
        }}
      />
    </Input.Wrapper>
  );
}
