import { Button, Group, Stack, Textarea } from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { Text } from "@mantine/core";
import {
  IconClick,
  IconFile,
  IconFileSearch,
  IconFileUpload,
} from "@tabler/icons-react";
import { Dropzone } from "@mantine/dropzone";
import { VariableSetter } from "../types";
import AnimateHeight from "react-animate-height";

export function CSVInput(props: VariableSetter<string>) {
  return (
    <>
      <TextInput {...props} />
      <DragAndDrop {...props} />
    </>
  );
}

function TextInput({
  label,
  description,
  value,
  setValue,
  validator,
  sampleData,
}: VariableSetter<string>) {
  const [hasError, setHasError] = useState<string | boolean>(false);

  const getSampleData = () => {
    let url = window.location.href + sampleData;
    if (import.meta.env.DEV) {
      url = `/${sampleData}`;
    }

    fetch(url).then((response) => {
      response.text().then((text) => {
        setValue(text);
      });
    });
  };

  useEffect(() => {
    if (validator) {
      setHasError(validator(value));
    }
  }, [value]);

  return (
    <div style={{ position: "relative" }}>
      {sampleData && (
        <Button
          pos="absolute"
          top={0}
          right={0}
          leftSection={<IconFileSearch />}
          onClick={getSampleData}
        >
          Load sample data
        </Button>
      )}
      <Textarea
        withAsterisk
        onDrop={(event) => {
          event.preventDefault();

          const file = event.dataTransfer.files[0];

          if (file) {
            readFile(file).then((text) => setValue(text));
          }
        }}
        autosize
        resize="vertical"
        minRows={10}
        maxRows={10}
        label={label}
        rightSection
        description={description}
        value={value}
        error={hasError}
        onChange={(event) => setValue(event.target.value as string)}
      />
    </div>
  );
}

function DragAndDrop({ file, value, setValue }: VariableSetter<string>) {
  const [hoveringFile, setHoveringFile] = useState(false);

  useEffect(() => {
    setHoveringFile(false);
  }, [value]);

  const fileProps = { size: "5rem", stroke: 1.5 };

  return (
    <AnimateHeight duration={300} height={value ? 0 : "auto"}>
      <Stack align="center">
        <Text fw={700} size="xl">
          OR
        </Text>
        <Dropzone
          w={"100%"}
          onDrop={async (files) => setValue(await readFile(files[0]))}
          onDragOver={() => {
            setHoveringFile(true);
          }}
          onDragLeave={() => {
            setHoveringFile(false);
          }}
          // 3 MB
          maxSize={3 * 1024 ** 2}
        >
          <Stack
            style={{
              pointerEvents: "none",
              border: `1px dashed ${hoveringFile ? "green" : "gray"}`,
              borderRadius: 5,
              padding: "1rem",
            }}
            align="center"
          >
            {hoveringFile ? (
              <IconFileUpload {...fileProps} color="green" />
            ) : (
              <Group>
                <IconFile {...fileProps} />
                <IconClick {...fileProps} />
              </Group>
            )}
            <Text size="xl" inline ta="center">
              Drag and drop a {file} or click to select
            </Text>
          </Stack>
        </Dropzone>
      </Stack>
    </AnimateHeight>
  );
}

async function readFile(file: File): Promise<string> {
  // Read the file
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      if (event.target) {
        resolve(
          event.target.result?.toString()?.replaceAll("\r\n", "\n") ?? ""
        );
      }
    };

    reader.onerror = (error) => {
      reject(error);
    };

    reader.readAsText(file);
  });
}
