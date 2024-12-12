import "@mantine/core/styles.css";

import { MantineProvider } from "@mantine/core";
import { theme } from "./theme";
import { SetupPredigMain } from "./pages/Setup.PredIG";

export default function App() {
  return (
    <MantineProvider theme={theme}>
      <SetupPredigMain />
    </MantineProvider>
  );
}
