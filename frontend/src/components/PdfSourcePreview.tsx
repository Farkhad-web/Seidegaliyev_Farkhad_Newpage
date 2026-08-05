import { AlertTriangle } from "lucide-react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// Per react-pdf's docs, the worker must be configured in the same module
// that renders <Document>/<Page> — setting it elsewhere (e.g. main.tsx) can
// be overwritten by module execution order.
pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();

interface Props {
  fileUrl: string;
  page: number;
}

export default function PdfSourcePreview({ fileUrl, page }: Props) {
  return (
    <Document
      file={fileUrl}
      loading={<PreviewSkeleton />}
      error={<PreviewError />}
      className="flex justify-center"
    >
      <Page
        pageNumber={page}
        width={340}
        loading={<PreviewSkeleton />}
        className="overflow-hidden rounded-md border border-ink-700"
      />
    </Document>
  );
}

function PreviewSkeleton() {
  return <div className="h-[440px] w-[340px] animate-pulse rounded-md bg-ink-800" />;
}

function PreviewError() {
  return (
    <div className="flex h-[200px] w-[340px] flex-col items-center justify-center gap-2 rounded-md border border-ink-700 bg-ink-800 text-center text-xs text-ink-400">
      <AlertTriangle className="h-4 w-4 text-amber-400" />
      Couldn't load the PDF preview.
    </div>
  );
}
