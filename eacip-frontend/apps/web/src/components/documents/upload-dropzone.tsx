"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

import { useUploadDocument } from "@/lib/documents/use-documents";

export function UploadDropzone() {
  const { mutate: upload, isPending, isError } = useUploadDocument();

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      acceptedFiles.forEach((file) => upload(file));
    },
    [upload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/tiff": [".tiff"],
    },
    multiple: true,
  });

  return (
    <div
      {...getRootProps()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
        isDragActive ? "border-slate-900 bg-slate-50" : "border-slate-300"
      }`}
    >
      <input {...getInputProps()} />
      {isPending ? (
        <p className="text-muted-foreground text-sm">Uploading…</p>
      ) : isDragActive ? (
        <p className="text-sm font-medium">Drop the file here</p>
      ) : (
        <>
          <p className="text-sm font-medium">
            Drag & drop a document, or click to browse
          </p>
          <p className="text-muted-foreground mt-1 text-xs">
            PDF, JPEG, PNG, or TIFF
          </p>
        </>
      )}
      {isError && (
        <p className="mt-2 text-xs text-red-600">
          Upload failed — check the file type and try again.
        </p>
      )}
    </div>
  );
}
