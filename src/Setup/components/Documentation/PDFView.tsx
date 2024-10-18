import { useCallback, useState } from "react";
import { useResizeObserver } from "@wojtekmaj/react-hooks";
import { Document, Page } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";

import type { PDFDocumentProxy } from "pdfjs-dist";
import { Button, Center, Group, Loader, Modal, Text } from "@mantine/core";
import { IconDownload } from "@tabler/icons-react";

const resizeObserverOptions = {};

import { pdfjs } from "react-pdf";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

export default function PDFView(props: { name: string; url: string }) {
  const [numPages, setNumPages] = useState<number>();
  const [containerRef, setContainerRef] = useState<HTMLElement | null>(null);
  const [containerWidth, setContainerWidth] = useState<number>();
  const [isLoaded, setIsLoaded] = useState(false);

  const onResize = useCallback<ResizeObserverCallback>((entries) => {
    const [entry] = entries;

    if (entry) {
      setContainerWidth(entry.contentRect.width);
    }
  }, []);

  useResizeObserver(containerRef, resizeObserverOptions, onResize);

  function onDocumentLoadSuccess({
    numPages: nextNumPages,
  }: PDFDocumentProxy): void {
    setNumPages(nextNumPages);
    setIsLoaded(true);
  }

  return (
    <>
      <Modal.Header>
        {isLoaded && (
          <Group align="center" w={containerWidth}>
            <Text size="xl" fw="bold">
              {props.name}
            </Text>
            <Button
              component="a"
              download
              href={props.url}
              leftSection={<IconDownload size={18} />}
            >
              Download
            </Button>
            <Modal.CloseButton />
          </Group>
        )}
      </Modal.Header>
      <Center ref={setContainerRef}>
        <Document
          file={props.url}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<Loader mt={30} mb={30} />}
        >
          {Array.from(new Array(numPages), (_el, index) => (
            <Page
              key={`page_${index + 1}`}
              pageNumber={index + 1}
              scale={1}
              width={containerWidth}
            />
          ))}
        </Document>
      </Center>
    </>
  );
}
