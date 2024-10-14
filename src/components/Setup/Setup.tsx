import {
  Button,
  Group,
  Image,
  Input,
  Modal,
  Radio,
  Stack,
  Tabs,
  TagsInput,
  Text,
  Textarea,
} from "@mantine/core";
import { useState } from "react";

import submit from "../../static/submit.png";

declare global {
  interface Window {
    horus: any;
  }
}
enum ModelTypes {
  PROVIDED = "provided",
  CUSTOM = "custom",
}

type PredIGVariables = {
  input_text: string;
  seed: number;
  model: string;
  modelXG: string;
  predig_model_type: ModelTypes;
  HLA_allele: string;
  peptide_len: string[];
  mat: string;
  alpha: number;
  precursor_len: number;
};

const PREDIG_MODELS = ["PredIG-NeoA", "PredIG-NonCan", "PredIG-Path"];
const DEFAULT_SETUP: PredIGVariables = {
  input_text: "",
  seed: Math.floor(Math.random() * 10000),
  predig_model_type: ModelTypes.PROVIDED,
  model: "",
  modelXG: PREDIG_MODELS[0],
  HLA_allele: "",
  peptide_len: ["8"],
  mat: "",
  alpha: 0.5,
  precursor_len: 9,
};

export function Setup() {
  const [prediIGVariables, setPrediIGVariables] = useState(DEFAULT_SETUP);

  const [isOverWithFile, setIsOverWithFile] = useState(false);

  return (
    <Stack m="lg" gap="lg">
      <div style={{ position: "relative" }}>
        <Textarea
          onDragOver={(event) => {
            event.preventDefault();
            setIsOverWithFile(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            setIsOverWithFile(false);
          }}
          onDrop={(event) => {
            event.preventDefault();
            setIsOverWithFile(false);

            // Read the file
            const reader = new FileReader();
            reader.onload = (event) => {
              if (event.target) {
                setPrediIGVariables({
                  ...prediIGVariables,
                  input_text: event.target.result as string,
                });
              }
            };
            reader.readAsText(event.dataTransfer.files[0]);
          }}
          autosize
          resize="vertical"
          minRows={10}
          maxRows={10}
          label="Input CSV/TSV"
          description="The file must have the following columns: peptide,allele,uniprot_id"
          value={prediIGVariables.input_text}
          onChange={(event) =>
            setPrediIGVariables({
              ...prediIGVariables,
              input_text: event.target.value,
            })
          }
        />
      </div>
      <Tabs
        defaultValue={ModelTypes.PROVIDED}
        onChange={(value) => {
          setPrediIGVariables({
            ...prediIGVariables,
            predig_model_type: (value as ModelTypes) ?? ModelTypes.PROVIDED,
            model:
              (value as ModelTypes) === ModelTypes.CUSTOM
                ? ""
                : PREDIG_MODELS[0],
          });
        }}
      >
        <Tabs.List>
          <Tabs.Tab value={ModelTypes.PROVIDED}>Provided models</Tabs.Tab>
          <Tabs.Tab value={ModelTypes.CUSTOM}>Custom model</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value={ModelTypes.PROVIDED}>
          <Radio.Group
            mt={25}
            value={prediIGVariables.model}
            onChange={(value) =>
              setPrediIGVariables({
                ...prediIGVariables,
                model: value,
              })
            }
            name="predig_model"
          >
            <Group mt="xs">
              {PREDIG_MODELS.map((model) => (
                <Radio key={model} value={model} label={model} />
              ))}
            </Group>
          </Radio.Group>
        </Tabs.Panel>
        <Tabs.Panel value={ModelTypes.CUSTOM}>
          <Group mt="xs" align="end">
            <Input
              flex={1}
              value={prediIGVariables.model}
              placeholder="model.pkl"
              onChange={(event) =>
                setPrediIGVariables({
                  ...prediIGVariables,
                  model: event.target.value,
                })
              }
            />
            <Button
              onClick={async () => {
                parent.horus.openExtensionFilePicker({
                  onFileConfirm: (path: string | null) => {
                    if (path) {
                      setPrediIGVariables({
                        ...prediIGVariables,
                        model: path,
                      });
                    }
                  },
                  allowedExtensions: [".pkl"],
                });
              }}
            >
              Browse...
            </Button>
          </Group>
        </Tabs.Panel>
      </Tabs>
      <Input.Wrapper label="HLA Allele">
        <Input
          value={prediIGVariables.HLA_allele}
          placeholder="HLA-A02:01"
          onChange={(e) =>
            setPrediIGVariables({
              ...prediIGVariables,
              HLA_allele: e.target.value,
            })
          }
        />
      </Input.Wrapper>
      <Input.Wrapper
        label="Peptide Length"
        description="Enter a number and press enter."
      >
        <TagsInput
          value={prediIGVariables.peptide_len}
          onChange={(value) => {
            if (value.length === 0) {
              setPrediIGVariables({
                ...prediIGVariables,
                peptide_len: [],
              });
              return;
            }

            // Check the value can be converted to integer
            const newValue = Number(value[value.length - 1]);
            if (Number.isInteger(newValue)) {
              setPrediIGVariables({
                ...prediIGVariables,
                peptide_len: value,
              });
            }
          }}
        />
      </Input.Wrapper>
      <Input.Wrapper label="Matrix">
        <Group mt="xs" align="end">
          <Input
            flex={1}
            value={prediIGVariables.mat}
            placeholder="tap.logodds.mat"
            onChange={(event) =>
              setPrediIGVariables({
                ...prediIGVariables,
                mat: event.target.value,
              })
            }
          />
          <Button
            onClick={async () => {
              parent.horus.openExtensionFilePicker({
                onFileConfirm: (path: string | null) => {
                  if (path) {
                    setPrediIGVariables({
                      ...prediIGVariables,
                      mat: path,
                    });
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
      <Input.Wrapper label="Alpha">
        <Input
          value={prediIGVariables.alpha}
          placeholder="0.5"
          onChange={(e) => {
            if (Number.isInteger(Number(e.target.value))) {
              setPrediIGVariables({
                ...prediIGVariables,
                alpha: Number(e.target.value),
              });
            }
          }}
        />
      </Input.Wrapper>
      <Input.Wrapper label="Precursor Length">
        <Input
          value={prediIGVariables.precursor_len}
          placeholder="9"
          onChange={(e) => {
            if (Number.isInteger(Number(e.target.value))) {
              setPrediIGVariables({
                ...prediIGVariables,
                precursor_len: Number(e.target.value),
              });
            }
          }}
        />
      </Input.Wrapper>
      <ConfigurationSavedModal predIGVariables={prediIGVariables} />
    </Stack>
  );
}

function ConfigurationSavedModal(props: { predIGVariables: PredIGVariables }) {
  const { predIGVariables } = props;
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Modal opened={isOpen} onClose={() => setIsOpen(false)} withCloseButton>
        <Text ta="center" size="lg" fw={700}>
          The PredIG configuration was correctly saved
        </Text>
        <Text ta="center">
          Close this setup view (Extensions → Close Extensions) and click on the
          "Play" button of the PredIG block
        </Text>
        <Image
          mt={20}
          src={submit}
          style={{
            borderRadius: 10,
            overflow: "hidden",
            // boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.5)",
          }}
        />
      </Modal>
      <Button
        color="green"
        onClick={() => {
          setIsOpen(true);
          parent.horus.setVariable(predIGVariables);
        }}
      >
        Save configuration
      </Button>
    </>
  );
}
