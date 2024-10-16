import { Button, Group, Input, Radio } from "@mantine/core";
import { VariableSetter } from "../types";

export const PREDIG_MODELS = ["PredIG-NeoA", "PredIG-NonCan", "PredIG-Path"];

export function SelectModel({ value, setValue }: VariableSetter<string>) {
  return (
    <Input.Wrapper label="Select Model">
      <Radio.Group
        value={value}
        onChange={setValue}
        name="predig_model"
        mt={10}
      >
        <Group>
          {PREDIG_MODELS.map((model) => (
            <Radio key={model} value={model} label={model} />
          ))}
        </Group>
      </Radio.Group>
    </Input.Wrapper>
  );
}

export function CustomModel({ value, setValue }: VariableSetter<string>) {
  return (
    <Group mt="xs" align="end">
      <Input
        flex={1}
        value={value}
        placeholder="model.pkl"
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
            allowedExtensions: [".pkl"],
          });
        }}
      >
        Browse...
      </Button>
    </Group>
  );
}
