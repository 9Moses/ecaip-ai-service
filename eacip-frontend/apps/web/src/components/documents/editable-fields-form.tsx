"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function humanizeFieldName(key: string): string {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function EditableFieldsForm({
  fields,
  onConfirm,
  isConfirming,
}: {
  fields: Record<string, unknown>;
  onConfirm: (fields: Record<string, unknown>) => void;
  isConfirming: boolean;
}) {
  const [values, setValues] = useState<Record<string, string>>(
    Object.fromEntries(
      Object.entries(fields).map(([k, v]) => [k, v == null ? "" : String(v)])
    )
  );

  function handleChange(key: string, value: string) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Convert empty strings back to null so we don't overwrite "unknown" with an empty string
    const cleaned = Object.fromEntries(
      Object.entries(values).map(([k, v]) => [k, v.trim() === "" ? null : v])
    );
    onConfirm(cleaned);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {Object.entries(values).map(([key, value]) => (
        <div key={key} className="flex flex-col gap-1.5">
          <Label htmlFor={key}>{humanizeFieldName(key)}</Label>
          <Input
            id={key}
            value={value}
            onChange={(e) => handleChange(key, e.target.value)}
            placeholder="Not found in document"
          />
        </div>
      ))}
      <Button type="submit" disabled={isConfirming} className="mt-2">
        {isConfirming ? "Confirming…" : "Confirm & Save"}
      </Button>
    </form>
  );
}
