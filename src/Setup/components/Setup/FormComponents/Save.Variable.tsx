import { Button, Image, Modal, Text } from "@mantine/core";
import { PredIGVariables } from "../types";
import { useState } from "react";
import submit from "../../../static/submit.png";

export function ConfigurationSavedModal(props: {
  predIGVariables: PredIGVariables;
}) {
  const { predIGVariables } = props;
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Modal
        opened={isOpen}
        onClose={() => setIsOpen(false)}
        withCloseButton
        centered
      >
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
