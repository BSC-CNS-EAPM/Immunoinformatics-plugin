import { Input } from "@mantine/core";
import { VariableSetter } from "../types";

export function Hallele({ value, setValue }: VariableSetter<string>) {
  return (
    <Input.Wrapper label="HLA Allele">
      <Input
        value={value}
        placeholder="HLA-A02:01"
        onChange={(e) => setValue(e.target.value)}
      />
    </Input.Wrapper>
  );
}
