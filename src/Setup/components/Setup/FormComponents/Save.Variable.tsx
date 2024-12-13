import { Center, Group, Image, Text } from "@mantine/core";
import submit from "../../../static/submit.png";
import { IconCircleCheck } from "@tabler/icons-react";

export function ConfigurationSavedModal() {
  return (
    <>
      <Group align="center" justify="center">
        <IconCircleCheck color="black" size={60} />
        <Text ta="center" size="lg" fw={700}>
          The PredIG configuration was correctly saved
        </Text>
      </Group>
      <Text>
        Close this setup view and click on the "Play" button of the PredIG
        block. Once the simulation is finished, you can visualize the results
        with the button that will appear on top of the block.
      </Text>
      <Center>
        <Image src={submit} miw="500px" radius={"lg"} />
      </Center>
    </>
  );
}
