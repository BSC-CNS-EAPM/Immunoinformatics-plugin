import "@mantine/core/styles.css";
import classes from "../main.module.css";

import {
  Alert,
  Badge,
  Button,
  Group,
  Loader,
  LoadingOverlay,
  MantineProvider,
  Pagination,
  Paper,
  Select,
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
  keepPreviousData,
  useQuery,
} from "@tanstack/react-query";
import { IconDownload, IconInfoCircle, IconTable } from "@tabler/icons-react";
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

type PredIGResult = Record<string, any>;

type ResultsApiResponse = {
  ok: boolean;
  results: PredIGResult[];
  columns: string[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  msg?: string;
};

function getURL(options?: {
  download?: boolean;
  fullSimulation?: boolean;
  page?: number;
  pageSize?: number;
}) {
  let csvPath = "";
  let urlPath = "";
  const path =
    "results_api" + (options?.download ? "/download_results/" : "/results/");
  if (import.meta.hot) {
    urlPath = window.location.origin + "/" + path;
    csvPath =
      "/home/perry/data/cdominguez/Immunoinformatics-plugin/PredIG_output.csv";
  } else {
    urlPath = window.location.href + path;
    csvPath = window.extensionData?.["csv"] as string;

    // Ensure HTTPS is present if the parent uses https
    if (
      parent.window.location.protocol === "https:" &&
      urlPath.startsWith("http:")
    ) {
      urlPath = urlPath.replace("http:", "https:");
    }
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

  if (options?.page) {
    url.searchParams.set("page", options.page.toString());
  }

  if (options?.pageSize) {
    url.searchParams.set("page_size", options.pageSize.toString());
  }

  return url.toString();
}

async function getDataFromHorus({
  page,
  pageSize,
}: {
  page: number;
  pageSize: number;
}): Promise<ResultsApiResponse> {
  try {
    const url = getURL({ page, pageSize });
    const response = await fetch(url);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || response.statusText);
    }

    const data = await response.json();

    if (!data.ok) {
      throw new Error(data.msg || "Unknown error");
    }

    return data as ResultsApiResponse;
  } catch (error) {
    throw error; // Re-throw to be caught by react-query
  }
}

function Welcome() {
  return (
    <>
      <Title className={classes.title} ta="center" mt={60}>
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
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(100);
  const [isDownloading, setIsDownloading] = useState(false);

  const { data, isLoading, isFetching, isError, error } = useQuery({
    queryKey: ["results", page, pageSize],
    queryFn: () => getDataFromHorus({ page, pageSize }),
    placeholderData: keepPreviousData,
  });

  const gridRef = useRef<AgGridReact>(null);

  if (isLoading) {
    return (
      <Stack align="center" my={50}>
        <Text size="lg" fw={500}>
          Loading results...
        </Text>
        <Loader color="blue" type="dots" size="lg" />
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
        {isError ? (error as Error).message : "No data found"}
      </Alert>
    );
  }

  const total = data.total ?? data.results.length;
  const totalPages = data.total_pages ?? 1;
  const startRow = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endRow = Math.min(page * pageSize, total);

  const colDef: ColDef[] = data.columns.map((col) => {
    return {
      filter: true,
      sortable: true,
      resizable: true,
      field: col,
      headerName: prettifyName(col),
      valueFormatter: (params) => {
        if (typeof params.value === "number") {
          if (Number.isInteger(params.value)) {
            return params.value.toString();
          }
          return params.value.toFixed(4);
        }
        return params.value;
      },
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

  const handlePageSizeChange = (val: string | null) => {
    if (val) {
      const newSize = Number(val);
      setPageSize(newSize);
      setPage(1);
    }
  };

  return (
    <Stack w="100%" gap="md" px={20} pb={40}>
      <Group justify="space-between" align="center" wrap="wrap">
        <Group gap="sm">
          <Badge variant="light" color="blue" size="lg" leftSection={<IconTable size={14} />}>
            Total: {total.toLocaleString()} rows
          </Badge>
          {isFetching && <Loader size="xs" color="blue" />}
        </Group>

        <Group gap="md">
          <Button
            variant="outline"
            leftSection={
              isDownloading ? <Loader color="blue" size="sm" /> : <IconDownload size={18} />
            }
            onClick={() => download(false)}
          >
            Download CSV
          </Button>
          <Button
            leftSection={
              isDownloading ? <Loader color="white" size="sm" /> : <IconDownload size={18} />
            }
            onClick={() => download(true)}
          >
            Download simulation
          </Button>
        </Group>
      </Group>

      {/* Grid container */}
      <Paper pos="relative" radius="md" withBorder p={0} style={{ overflow: "hidden" }}>
        <LoadingOverlay visible={isFetching && !isLoading} zIndex={1000} overlayProps={{ radius: "sm", blur: 1 }} />
        <div
          className="ag-theme-quartz"
          style={{
            height: "550px",
            width: "100%",
          }}
        >
          <AgGridReact
            ref={gridRef}
            rowData={data.results}
            columnDefs={colDef}
            defaultColDef={{
              flex: 1,
              minWidth: 160,
              sortable: true,
              filter: true,
              resizable: true,
            }}
          />
        </div>
      </Paper>

      {/* Pagination Controls */}
      <Paper radius="md" withBorder p="md">
        <Group justify="space-between" align="center" wrap="wrap" gap="md">
          <Text size="sm" c="dimmed">
            {total > 0
              ? `Showing ${startRow.toLocaleString()} - ${endRow.toLocaleString()} of ${total.toLocaleString()} entries`
              : "No entries to display"}
          </Text>

          <Group gap="lg">
            <Pagination
              value={page}
              onChange={setPage}
              total={totalPages}
              boundaries={1}
              siblings={1}
              size="sm"
              withEdges
            />

            <Group gap="xs" align="center">
              <Text size="sm" c="dimmed">
                Rows per page:
              </Text>
              <Select
                value={pageSize.toString()}
                onChange={handlePageSizeChange}
                data={["25", "50", "100", "250", "500", "1000"]}
                w={90}
                size="xs"
                allowDeselect={false}
              />
            </Group>
          </Group>
        </Group>
      </Paper>
    </Stack>
  );
}

function prettifyName(name: string) {
  if (!name) return "";
  const specialCases: Record<string, string> = {
    predig: "PredIG",
    tap: "TAP",
    noah: "NOAH",
    netcleave: "NetCleave",
    id: "ID",
    epitope: "Epitope",
    hla_allele: "HLA Allele",
    charge_peptide: "Charge (Peptide)",
    charge_tcr_contact: "Charge (TCR Contact)",
    hydroph_peptide: "Hydrophobicity (Peptide)",
    hydroph_tcr_contact: "Hydrophobicity (TCR Contact)",
    mw_peptide: "MW (Peptide)",
    mw_tcr_contact: "MW (TCR Contact)",
    stab_peptide: "Stability (Peptide)",
    tcr_contact: "TCR Contact",
    mhcflurry_affinity: "MHCflurry Affinity",
    mhcflurry_affinity_percentile: "MHCflurry Affinity %",
    mhcflurry_best_allele: "MHCflurry Best Allele",
    mhcflurry_presentation_percentile: "MHCflurry Presentation %",
    mhcflurry_presentation_score: "MHCflurry Presentation Score",
    mhcflurry_processing_score: "MHCflurry Processing Score",
  };
  const lower = name.toLowerCase();
  if (specialCases[lower]) {
    return specialCases[lower];
  }
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
