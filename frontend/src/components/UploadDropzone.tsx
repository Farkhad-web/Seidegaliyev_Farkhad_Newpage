import { useRef, useState } from "react";

interface Props {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

export function UploadDropzone({ onFiles, disabled }: Props) {
  const [isOver, setIsOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsOver(true);
      }}
      onDragLeave={() => setIsOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsOver(false);
        if (disabled) return;
        onFiles(Array.from(e.dataTransfer.files));
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`cursor-pointer rounded-xl border-2 border-dashed p-4 text-center text-xs transition-colors ${
        isOver ? "border-brand-400 bg-brand-500/10 text-brand-200" : "border-ink-600 text-ink-400 hover:border-ink-500"
      } ${disabled ? "cursor-not-allowed opacity-50" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.txt,.md"
        className="hidden"
        disabled={disabled}
        onChange={(e) => {
          if (e.target.files) onFiles(Array.from(e.target.files));
          e.target.value = "";
        }}
      />
      <div className="text-lg">📄</div>
      <div className="mt-1 font-medium text-ink-200">Drop files or click to upload</div>
      <div className="mt-0.5 text-ink-500">PDF, TXT, MD · up to 20MB</div>
    </div>
  );
}
