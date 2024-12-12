import { Button, Group, Input } from "@mantine/core";
import { VariableSetter } from "../types";

export function Hallele({ value, setValue }: VariableSetter<string>) {
  return (
    <Input.Wrapper label="Matrix">
      <Group mt="xs" align="end">
        <Input
          flex={1}
          value={value}
          placeholder="tap.logodds.mat"
          onChange={(event) => setValue(event.target.value)}
        />
        <Button
          onClick={async () => {
            parent.horus.openExtensionFilePicker({
              onFileConfirm: (path: string | null) => {
                if (path) {
                  setValue(path);
                }
              },
              allowedExtensions: [".mat"],
            });
          }}
        >
          Browse...
        </Button>
      </Group>
    </Input.Wrapper>
  );
}
