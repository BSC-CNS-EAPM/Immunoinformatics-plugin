import {
  Alert,
  Button,
  Center,
  Container,
  Group,
  Image,
  Stack,
  Text,
} from "@mantine/core";
import submit from "../../../static/submit.png";
import {
  IconArrowUpRight,
  IconCircleCheck,
  IconInfoCircle,
} from "@tabler/icons-react";

export function ConfigurationSavedModal() {
  return (
    <Container>
      <Stack align="center">
        <Group align="center" justify="center">
          <IconCircleCheck color="black" size={60} />
          <Text ta="center" size="lg" fw={700}>
            The PredIG configuration was correctly saved
          </Text>
        </Group>
        <Button
          rightSection={<IconArrowUpRight size={16} />}
          onClick={async () => {
            const placedID = await window.horusVariable.getVariable().placedID;
            parent.horus.executeFlow({ placedID: placedID });
            parent.horus.closeTab();
          }}
        >
          Execute simulation & close setup
        </Button>
        <Alert
          icon={<IconInfoCircle />}
          color="blue"
          radius="md"
          variant="light"
        >
          You can either click the button above to execute the simulation and
          close this setup tab, or manually close this tab and click the "Play"
          button on the PredIG block to start the simulation. After completion,
          view results using the button that appears above the block.
        </Alert>
        <Center>
          <Image src={submit} miw="500px" radius={"lg"} />
        </Center>
      </Stack>
    </Container>
  );
}
