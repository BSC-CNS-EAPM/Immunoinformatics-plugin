import {
  IconBook2,
  IconBrandDocker,
  IconBrandGithub,
  IconCircleLetterA,
  IconDownload,
  IconFileTypeCsv,
  IconListCheck,
} from "@tabler/icons-react";
import { Button, Group, Modal, Stack, Text } from "@mantine/core";
import { useState } from "react";
import PDFView from "./PDFView";

const docs = [
  {
    label: "Abstract",
    icon: <IconBook2 size={18} />,
    view: <PDFView url="./oct_predig_abstract_web.pdf" name="Abstract" />,
  },
  {
    label: "Instructions",
    icon: <IconListCheck size={18} />,
    view: <PDFView url="./predig_instructions_web.pdf" name="Instructions" />,
  },
  {
    label: "Output format",
    icon: <IconFileTypeCsv size={18} />,
    view: <PDFView url="./predig_outputformat_web.pdf" name="Output format" />,
  },
  {
    label: "Downloads",
    icon: <IconDownload size={18} />,
    view: <DownloadsView />,
  },
];

export function DocumentationButton() {
  const [currentView, setCurrentView] = useState<null | JSX.Element>(null);

  return (
    <>
      <Group gap="sm" justify="center">
        {docs.map((doc) => (
          <Button
            leftSection={doc.icon}
            variant="outline"
            onClick={() => {
              setCurrentView(doc.view);
            }}
          >
            {doc.label}
          </Button>
        ))}
      </Group>
      <Modal
        size={"100%"}
        centered
        opened={!!currentView}
        onClose={() => {
          setCurrentView(null);
        }}
        withCloseButton={false}
      >
        {currentView}
      </Modal>
    </>
  );
}

function DownloadsView() {
  return (
    <Stack>
      <Group gap={10} justify="center">
        <IconDownload size="35px" />
        <Text size="35px" fw={700}>
          Downloads
        </Text>
      </Group>
      <Text ta={"center"}>
        Find more information about{" "}
        <Text span fw="bold">
          PredIG
        </Text>{" "}
        here:
      </Text>
      <Button
        component="a"
        href="https://github.com/BSC-CNS-EAPM/PredIG"
        target="_blank"
        leftSection={<IconBrandGithub />}
      >
        PredIG repo
      </Button>
      <Button leftSection={<IconBrandDocker />}>PredIG Docker</Button>
      <Button leftSection={<IconCircleLetterA />}>PredIG Singularity</Button>
    </Stack>
  );
}
