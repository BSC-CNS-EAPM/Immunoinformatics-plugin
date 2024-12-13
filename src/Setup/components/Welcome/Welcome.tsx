import { Center, Text, Title } from "@mantine/core";
import classes from "../../../main.module.css";
import { DocumentationButton } from "../Documentation/Documentation";

export function Welcome() {
  return (
    <>
      <Title className={classes.title} ta="center" mt={20}>
        <Text
          inherit
          variant="gradient"
          component="span"
          gradient={{ from: "purple", to: "yellow" }}
        >
          PredIG
        </Text>
      </Title>
      <Center mt={25}>
        <DocumentationButton />
      </Center>
    </>
  );
}
