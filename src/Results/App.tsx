import "@mantine/core/styles.css";
import classes from "../main.module.css";

import {
  Alert,
  Button,
  Center,
  Group,
  Loader,
  MantineProvider,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { theme } from "./theme";

import "ag-grid-community/styles/ag-grid.css"; // grid core CSS
import "ag-grid-community/styles/ag-theme-quartz.css"; // optional theme
import { AgGridReact } from "ag-grid-react";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { IconDownload, IconInfoCircle } from "@tabler/icons-react";
import { ColDef } from "ag-grid-community";
import { useRef, useState } from "react";

// Create a client
const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme}>
        <Stack align="center" gap={50} style={{ overflow: "hidden" }}>
          <Welcome />
          <PredIGResults />
        </Stack>
      </MantineProvider>
    </QueryClientProvider>
  );
}

declare global {
  interface Window {
    extensionData: Record<string, any>;
  }
}

type PredIGResult = {
  NOAH: number;
  TAP: number;
  charge_peptide: number;
  charge_tcr_contact: number;
  epitope: string;
  epitope_noah: string;
  epitope_tapmap: string;
  epitope_x: string;
  epitope_y: string;
  hla_allele: string;
  hla_allele_noah: string;
  hydroph_peptide: number;
  hydroph_tcr_contact: number;
  id: string;
  mhcflurry_affinity: number;
  mhcflurry_affinity_percentile: number;
  mhcflurry_best_allele: string;
  mhcflurry_presentation_percentile: number;
  mhcflurry_presentation_score: number;
  mhcflurry_processing_score: number;
  mw_peptide: number;
  mw_tcr_contact: number;
  netcleave: number;
  predig: number;
  stab_peptide: number;
  tcr_contact: number;
};

function getURL(options?: { download?: boolean; fullSimulation?: boolean }) {
  let csvPath = "";
  let urlPath = "";
  const path =
    "results_api" + (options?.download ? "/download_results" : "/results");
  if (import.meta.hot) {
    urlPath = window.location.origin + "/" + path;
    csvPath =
      "/home/perry/data/cdominguez/Immunoinformatics-plugin/PredIG_output.csv";
  } else {
    urlPath = window.location.href + path;
    csvPath = window.extensionData?.["csv"] as string;
  }

  if (!csvPath) {
    throw new Error("No CSV file found");
  }

  const url = new URL(urlPath);
  url.searchParams.set("csv", csvPath);

  if (options?.download) {
    url.searchParams.set("name", parent.horus.getFlow().name);
  }

  if (options?.fullSimulation) {
    url.searchParams.set("simulation", "true");
  }

  return url.toString();
}

async function getDataFromHorus() {
  try {
    const response = await fetch(getURL());

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || response.statusText);
    }

    const data = await response.json();

    if (!data.ok) {
      throw new Error(data.msg || "Unknown error");
    }

    return data as {
      results: PredIGResult[];
      columns: string[];
    };
  } catch (error) {    throw error; // Re-throw to be caught by react-query
  }
}

function Welcome() {
  return (
    <>
      <Title className={classes.title} ta="center" mt={100}>
        <Text
          inherit
          variant="gradient"
          component="span"
          gradient={{ from: "purple", to: "yellow" }}
        >
          PredIG
        </Text>{" "}
        Results
      </Title>
    </>
  );
}

function downloadFile(fullSimulation: boolean) {
  const url = getURL({ download: true, fullSimulation: fullSimulation });

  const a = document.createElement("a");

  a.href = url;
  a.download = `predig_results.${fullSimulation ? "zip" : "csv"}`;

  a.click();

  a.remove();
}

function PredIGResults() {
  const [isDownloading, setIsDownloading] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["results"],
    queryFn: getDataFromHorus,
  });

  const gridRef = useRef<AgGridReact>(null);

  if (isLoading) {
    return (
      <Stack align="center">
        Loading results...
        <Loader color="blue" />
      </Stack>
    );
  }

  if (!data || isError) {
    return (
      <Alert
        variant="light"
        color="red"
        title="Error"
        icon={<IconInfoCircle size={36} />}
      >
        {isError ? error.message : "No data found"}
      </Alert>
    );
  }

  const colDef: ColDef[] = data.columns.map((col) => {
    return {
      filter: true,
      field: col,
      header: prettifyName(col),
      headerName: prettifyName(col),
    };
  });

  function download(simulation: boolean) {
    setIsDownloading(true);

    try {
      downloadFile(simulation);
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <Stack w="100%">
      <Group gap={20} align="center" justify="center">
        <Button
          w={200}
          leftSection={
            isDownloading ? <Loader color="black" /> : <IconDownload />
          }
          onClick={() => download(false)}
        >
          Download CSV
        </Button>
        <Button
          w={250}
          leftSection={
            isDownloading ? <Loader color="black" /> : <IconDownload />
          }
          onClick={() => download(true)}
        >
          Download simulation
        </Button>
      </Group>
      <div
        className="ag-theme-quartz" // applying the Data Grid theme
        style={{
          minHeight: "10px",
          width: "100%",
          overflow: "hidden",
          padding: 20,
        }} // the Data Grid will fill the size of the parent container
      >
        <AgGridReact
          ref={gridRef}
          rowData={data.results}
          columnDefs={colDef}
          domLayout="autoHeight"
          defaultColDef={{
            flex: 1,
            minWidth: 200,
          }}
        />
      </div>
    </Stack>
  );
}

function prettifyName(name: string) {
  return name;
}
