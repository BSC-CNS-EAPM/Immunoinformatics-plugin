import "@mantine/core/styles.css";

import { MantineProvider } from "@mantine/core";
import { theme } from "./theme";
import { SetupTCoaRseMain } from "./pages/Setup.TCoaRse";

export default function App() {
  return (
    <MantineProvider theme={theme}>
      <SetupTCoaRseMain />
    </MantineProvider>
  );
}
