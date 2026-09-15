import { useEffect, useRef, useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  Checkbox,
  Container,
  Divider,
  FileInput,
  Group,
  Loader,
  NumberInput,
  Paper,
  Progress,
  SimpleGrid,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  IconAdjustments,
  IconAlertTriangle,
  IconArrowUpRight,
  IconCircleCheck,
  IconFolderOpen,
  IconInfoCircle,
  IconLicense,
  IconPlayerPlay,
  IconUpload,
} from "@tabler/icons-react";

import type { TCoaRseSettings } from "../types";

/** The eight steps the block runs, in the order the pipeline needs them. */
const STEPS = [
  "Copy Models",
  "Structure Metadata",
  "Contact Maps",
  "pyDock Energies",
  "Pairwise DockQ",
  "Energetic Scorer",
  "Merge Energies",
  "TCoaRse Predictor",
];

/** Mirrors the defaults of the block variables, so an untouched page saves
 *  exactly what the block would have used on its own. */
const DEFAULTS: TCoaRseSettings = {
  af3_dir: "",
  chain_map: "D:E:C:B:A",
  not_experimental: true,
  energy_threshold: 7,
  io_workers: 8,
  chunk_size: 5000,
  pydock_modules: "bindEy",
  model: "",
  accepted_non_commercial: false,
  accepted_af3_terms: false,
};

/** Bytes as the closest readable unit, e.g. "412.3 MB". */
function formatBytes(bytes: number): string {
  const units = ["B", "kB", "MB", "GB"];
  let value = bytes;
  let unit = 0;

  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }

  return `${value.toFixed(value < 10 && unit > 0 ? 1 : 0)} ${units[unit]}`;
}

export function SetupTCoaRseMain() {
  const [settings, setSettings] = useState<TCoaRseSettings>(DEFAULTS);
  const [saved, setSaved] = useState(false);
  const [archive, setArchive] = useState<File | null>(null);
  const [phase, setPhase] = useState<"idle" | "uploading" | "extracting">(
    "idle"
  );
  const [sent, setSent] = useState(0);
  const uploadRequest = useRef<XMLHttpRequest | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadInfo, setUploadInfo] = useState<string | null>(null);

  // On first open, load whatever the block already holds
  useEffect(() => {
    const variable = window?.horusVariable?.getVariable?.();

    if (variable?.value) {
      setSettings({ ...DEFAULTS, ...variable.value });
    }
  }, []);

  // Push every edit back to the block
  useEffect(() => {
    window?.horusVariable?.setVariable?.(settings);
  }, [settings]);

  const update = <K extends keyof TCoaRseSettings>(
    key: K,
    value: TCoaRseSettings[K]
  ) => setSettings((current) => ({ ...current, [key]: value }));

  /**
   * Pick the folder with the native explorer of Horus.
   *
   * The page is served from the Horus server, so it is same-origin with the
   * window hosting it and can call its API; the iframe itself only gets
   * `horusVariable` injected.
   */
  const browseFolder = async () => {
    const picked = await parent?.horus?.openExtensionFilePicker?.({
      openFolder: true,
    });

    if (picked) {
      update("af3_dir", picked);
      setUploadInfo(null);
      setUploadError(null);
    }
  };

  /**
   * Send the archive to the page endpoint, which extracts it into the flow
   * folder and answers with the folder the pipeline should run on.
   */
  /**
   * Send the archive to the page endpoint, which extracts it into the flow
   * folder and answers with the folder the pipeline should run on.
   *
   * XMLHttpRequest rather than fetch: fetch cannot report upload progress, and
   * these archives are large enough that a button reading "Uploading..." for
   * several minutes is indistinguishable from a hang. It also gives a usable
   * abort().
   */
  const uploadArchive = () => {
    if (!archive) {
      return;
    }

    setUploadError(null);
    setUploadInfo(null);
    setSent(0);
    setPhase("uploading");

    const flowPath = parent?.horus?.getFlow?.()?.path;

    const body = new FormData();
    body.append("archive", archive);
    body.append("flow_path", flowPath ?? "");

    const request = new XMLHttpRequest();
    uploadRequest.current = request;

    request.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        setSent(event.loaded);

        // The server only starts extracting once it holds the whole archive,
        // and it cannot report on that over a request that is already sent.
        // So the bar is honest up to here and indeterminate afterwards.
        if (event.loaded >= event.total) {
          setPhase("extracting");
        }
      }
    };

    request.onload = () => {
      uploadRequest.current = null;
      setPhase("idle");

      let data: { ok?: boolean; msg?: string; af3_dir?: string; folders?: number; sample?: string[] };

      try {
        data = JSON.parse(request.responseText);
      } catch {
        setUploadError(`The server answered with ${request.status}`);
        return;
      }

      if (!data.ok) {
        setUploadError(data.msg ?? "The archive could not be extracted");
        return;
      }

      update("af3_dir", data.af3_dir ?? "");
      setUploadInfo(
        `Extracted ${data.folders} folders` +
          (data.sample?.length ? ` (${data.sample.join(", ")}...)` : "")
      );
    };

    request.onerror = () => {
      uploadRequest.current = null;
      setPhase("idle");
      setUploadError("The upload failed");
    };

    request.onabort = () => {
      uploadRequest.current = null;
      setPhase("idle");
      setUploadError("The upload was cancelled");
    };

    request.open("POST", "tcoarse_api/upload_af3/");
    request.send(body);
  };

  const cancelUpload = () => uploadRequest.current?.abort();

  /**
   * The threshold is only meaningful with a model of your own: the pretrained
   * one was fit on features built at the default. Clearing the model puts the
   * threshold back, so a value set for a custom model is never left behind to
   * be used silently with the pretrained one.
   */
  const setModel = (model: string) =>
    setSettings((current) => ({
      ...current,
      model,
      energy_threshold: model.trim()
        ? current.energy_threshold
        : DEFAULTS.energy_threshold,
    }));

  const hasCustomModel = Boolean(settings.model.trim());

  const busy = phase !== "idle";
  const percent = archive && archive.size ? (sent / archive.size) * 100 : 0;

  if (saved) {
    return (
      <ConfigurationSaved
        accepted={{
          nonCommercial: settings.accepted_non_commercial,
          af3Terms: settings.accepted_af3_terms,
        }}
        setAccepted={(value) =>
          setSettings((current) => ({
            ...current,
            accepted_non_commercial: value.nonCommercial,
            accepted_af3_terms: value.af3Terms,
          }))
        }
      />
    );
  }

  return (
    <Container my="lg">
      <Stack gap="lg">
        <Stack gap="xs" align="center">
          <Title order={2} ta="center">
            <Text
              inherit
              component="span"
              variant="gradient"
              gradient={{ from: "purple", to: "yellow" }}
            >
              TCoaRse
            </Text>{" "}
            Pipeline
          </Title>
          <Text size="sm" c="dimmed" ta="center" maw={520}>
            Scores TCR-pMHC models from a folder of AlphaFold3 predictions.
            Every step runs as a single job, keeping all its intermediate
            outputs.
          </Text>
        </Stack>

        <Paper withBorder radius="md" p="md" bg="var(--mantine-color-gray-0)">
          <Group gap="xs" mb="sm">
            <IconInfoCircle size={16} />
            <Text size="sm" fw={600}>
              {STEPS.length} steps, in order
            </Text>
          </Group>
          <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="xs">
            {STEPS.map((step, index) => (
              <Group key={step} gap={6} wrap="nowrap">
                <Badge size="sm" circle variant="light">
                  {index + 1}
                </Badge>
                <Text size="xs" style={{ lineHeight: 1.2 }}>
                  {step}
                </Text>
              </Group>
            ))}
          </SimpleGrid>
        </Paper>

        <Card withBorder radius="md" padding="md">
          <Group gap="xs" mb="md">
            <ThemeIcon variant="light" size="sm">
              <IconFolderOpen size={14} />
            </ThemeIcon>
            <Text fw={600}>Input</Text>
          </Group>

          <Stack gap="xs">
          <Group align="flex-end" gap="xs" wrap="nowrap">
            <TextInput
              required
              style={{ flex: 1 }}
              label="AF3 outputs folder"
              description="Folder holding the AlphaFold3 predictions, one subfolder per TCR."
              placeholder="/path/to/af3_outputs"
              value={settings.af3_dir}
              onChange={(event) => update("af3_dir", event.currentTarget.value)}
            />
            <Button
              variant="default"
              leftSection={<IconFolderOpen size={16} />}
              onClick={browseFolder}
            >
              Browse...
            </Button>
          </Group>

          <Text size="xs" c="dimmed">
            Browse picks a folder on the machine running Horus. Upload an
            archive instead when the predictions live somewhere else.
          </Text>

          <Group align="flex-end" gap="xs" wrap="nowrap">
            <FileInput
              style={{ flex: 1 }}
              label="Or upload an archive"
              description="A .tar, .tar.gz, .tgz or .zip of the AF3 outputs folder."
              placeholder="Choose an archive..."
              accept=".tar,.tar.gz,.tgz,.tar.bz2,.tar.xz,.zip"
              value={archive}
              onChange={setArchive}
              disabled={busy}
            />
            <Button
              leftSection={
                busy ? <Loader size={16} /> : <IconUpload size={16} />
              }
              disabled={!archive || busy}
              onClick={uploadArchive}
            >
              {busy ? "Working..." : "Upload"}
            </Button>
            {busy && (
              <Button variant="default" color="red" onClick={cancelUpload}>
                Cancel
              </Button>
            )}
          </Group>

          {busy && (
            <Stack gap={4}>
              <Progress
                value={phase === "uploading" ? percent : 100}
                animated={phase === "extracting"}
                striped={phase === "extracting"}
              />
              <Group justify="space-between">
                <Text size="xs" c="dimmed">
                  {phase === "uploading"
                    ? `Uploading... ${percent.toFixed(0)}%`
                    : "Extracting on the server..."}
                </Text>
                {phase === "uploading" && archive && (
                  <Text size="xs" c="dimmed">
                    {formatBytes(sent)} / {formatBytes(archive.size)}
                  </Text>
                )}
              </Group>
            </Stack>
          )}

          {uploadError && (
            <Alert
              icon={<IconAlertTriangle />}
              color="red"
              variant="light"
              withCloseButton
              onClose={() => setUploadError(null)}
            >
              {uploadError}
            </Alert>
          )}

          {uploadInfo && (
            <Alert icon={<IconCircleCheck />} color="green" variant="light">
              {uploadInfo}
            </Alert>
          )}
          </Stack>
        </Card>

        <Card withBorder radius="md" padding="md">
          <Group gap="xs" mb="md">
            <ThemeIcon variant="light" size="sm" color="grape">
              <IconAdjustments size={14} />
            </ThemeIcon>
            <Text fw={600}>Parameters</Text>
          </Group>

          <Stack gap="md">
            <TextInput
              label="Chain map"
              description="Chain mapping used by the contact maps and the energetic scorer."
              value={settings.chain_map}
              onChange={(event) =>
                update("chain_map", event.currentTarget.value)
              }
            />

            <Switch
              label="Predicted structures"
              description="The models come from a predictor, not from an experiment."
              checked={settings.not_experimental}
              onChange={(event) =>
                update("not_experimental", event.currentTarget.checked)
              }
            />

            <TextInput
              label="TCoaRse model"
              description="Overrides the model set in the TCoaRse configuration."
              placeholder="Optional"
              value={settings.model}
              onChange={(event) => setModel(event.currentTarget.value)}
            />

            <NumberInput
              label="Contact threshold"
              description={
                hasCustomModel
                  ? "Distance threshold of the energetic scorer, in angstrom."
                  : `Fixed at ${DEFAULTS.energy_threshold} A: the pretrained model was trained on features built with it. Set a model of your own to change it.`
              }
              min={1}
              disabled={!hasCustomModel}
              value={settings.energy_threshold}
              onChange={(value) =>
                update(
                  "energy_threshold",
                  Number(value) || DEFAULTS.energy_threshold
                )
              }
            />
          </Stack>
        </Card>


        <Divider />

        <Group justify="space-between" align="center">
          <Text size="xs" c="dimmed">
            {settings.af3_dir.trim()
              ? "Ready to run."
              : "Set the AF3 outputs folder to continue."}
          </Text>
          <Button
            size="md"
            leftSection={<IconPlayerPlay size={16} />}
            disabled={!settings.af3_dir.trim() || busy}
            onClick={() => setSaved(true)}
          >
            Save configuration
          </Button>
        </Group>
      </Stack>
    </Container>
  );
}

/**
 * The screen shown once the configuration is saved.
 *
 * Running is gated behind two explicit confirmations rather than one generic
 * "I accept the terms": the AlphaFold3 output terms restrict commercial use,
 * so the user states that neither they nor their organisation is a commercial
 * entity, and separately that their use of the AF3 output complies with the
 * applicable terms. The wording also keeps TCoaRse described as what it is --
 * a tool that scores structures that already exist, not one that predicts
 * them -- since that distinction is what puts it outside the restriction on
 * AlphaFold3-like structure prediction.
 */
function ConfigurationSaved({
  accepted,
  setAccepted,
}: {
  accepted: { nonCommercial: boolean; af3Terms: boolean };
  setAccepted: (value: { nonCommercial: boolean; af3Terms: boolean }) => void;
}) {
  const canRun = accepted.nonCommercial && accepted.af3Terms;

  return (
    <Container my="lg">
      <Stack align="center" gap="lg" mt="xl">
        <ThemeIcon size={72} radius="xl" variant="light" color="green">
          <IconCircleCheck size={44} />
        </ThemeIcon>
        <Stack gap={4} align="center">
          <Title order={3} ta="center">
            Configuration saved
          </Title>
          <Text size="sm" c="dimmed" ta="center">
            The TCoaRse pipeline is ready to run.
          </Text>
        </Stack>

        <Card withBorder radius="md" padding="md" w="100%">
          <Group gap="xs" mb="sm">
            <ThemeIcon variant="light" size="sm" color="orange">
              <IconLicense size={14} />
            </ThemeIcon>
            <Text fw={600}>Terms of use</Text>
          </Group>

          <Text size="sm" c="dimmed" mb="md">
            TCoaRse evaluates and scores TCR-pMHC structures that already
            exist. It does not predict or generate structures. Its input is the
            output of AlphaFold3, whose terms restrict how that output may be
            used, so please confirm both points below before running.
          </Text>

          <Stack gap="sm">
            <Checkbox
              checked={accepted.nonCommercial}
              onChange={(event) =>
                setAccepted({
                  ...accepted,
                  nonCommercial: event.currentTarget.checked,
                })
              }
              label={
                <Text size="sm">
                  I confirm that neither I nor my organisation is a commercial
                  entity, and that this analysis is not carried out for
                  commercial purposes.
                </Text>
              }
            />
            <Checkbox
              checked={accepted.af3Terms}
              onChange={(event) =>
                setAccepted({
                  ...accepted,
                  af3Terms: event.currentTarget.checked,
                })
              }
              label={
                <Text size="sm">
                  I confirm that my use of the AlphaFold3 output supplied to
                  this pipeline complies with the terms applicable to it.
                </Text>
              }
            />
          </Stack>
        </Card>

        <Button
          rightSection={<IconArrowUpRight size={16} />}
          disabled={!canRun}
          onClick={async () => {
            const placedID = await window.horusVariable?.getVariable()?.placedID;

            if (placedID) {
              parent.horus.executeFlow({ placedID });
              parent.horus.closeTab();
            }
          }}
        >
          Execute pipeline & close setup
        </Button>

        {!canRun && (
          <Text size="xs" c="dimmed" ta="center">
            Confirm both statements above to run the pipeline.
          </Text>
        )}
      </Stack>
    </Container>
  );
}
