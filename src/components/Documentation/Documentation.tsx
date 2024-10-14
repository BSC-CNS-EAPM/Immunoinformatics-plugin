import { IconBook2 } from "@tabler/icons-react";
import { Anchor, Button } from "@mantine/core";
export function DocumentationButton() {
  //   const docsURL = `${window.location.href}predig_server_readmes.pdf`;
  const docsURL = `${window.location.href}predig_server_readmes.pdf`;

  return (
    <>
      <Anchor href={docsURL} target="_blank" download>
        <Button leftSection={<IconBook2 size={18} />} variant="outline">
          Documentation
        </Button>
      </Anchor>
    </>
  );
}
