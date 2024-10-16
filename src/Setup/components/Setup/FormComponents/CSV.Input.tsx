import { Stack, Textarea } from "@mantine/core";
import { useEffect, useState } from "react";
import { Text } from "@mantine/core";
import { IconFile, IconFileUpload } from "@tabler/icons-react";
import { Dropzone } from "@mantine/dropzone";
import { VariableSetter } from "../types";
import AnimateHeight from "react-animate-height";

export function CSVInput(props: VariableSetter<string>) {
  const [isOverWithFile, setIsOverWithFile] = useState(false);

  return (
    <>
      <TextInput {...props} />
      <DragAndDrop {...props} />
    </>
  );
}

function TextInput({ value, setValue }: VariableSetter<string>) {
  return (
    <Textarea
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
      label="Input CSV/TSV"
      description="The input must have the following columns: peptide,allele,uniprot_id"
      value={value}
      onChange={(event) => setValue(event.target.value as string)}
    />
  );
}

function DragAndDrop({ value, setValue }: VariableSetter<string>) {
  const [hoveringFile, setHoveringFile] = useState(false);

  useEffect(() => {
    setHoveringFile(false);
  }, [value]);

  const fileProps = { size: "5rem", stroke: 1.5 };

  return (
    <AnimateHeight duration={300} height={value ? 0 : "auto"}>
      <Stack align="center">
        <Text>OR</Text>
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
              <IconFile {...fileProps} />
            )}

            <Text size="xl" inline ta="center">
              Drag a CSV/TSV file here or click to select files
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
        resolve(event.target.result?.toString() ?? "");
      }
    };

    reader.onerror = (error) => {
      reject(error);
    };

    reader.readAsText(file);
  });
}
