"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface SectionFormProps {
  section: string;
  fields: string[];
  initialData?: Record<string, string | string[]>;
  onSave?: (data: Record<string, string | string[]>) => void;
  onAiSuggest?: (section: string) => Promise<string>;
}

export function SectionForm({
  section,
  fields,
  initialData = {},
  onSave,
  onAiSuggest,
}: SectionFormProps) {
  const [data, setData] = useState<Record<string, string>>(
    Object.fromEntries(
      fields.map((f) => {
        const val = initialData[f];
        return [f, Array.isArray(val) ? val.join("\n") : (val ?? "")];
      })
    )
  );
  const [suggesting, setSuggesting] = useState(false);

  const handleChange = (field: string, value: string) => {
    setData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    onSave?.(data);
  };

  const handleAiSuggest = async () => {
    if (!onAiSuggest) return;
    setSuggesting(true);
    try {
      const suggestion = await onAiSuggest(section);
      console.log("AI suggestion:", suggestion);
    } catch (err) {
      console.error(err);
    } finally {
      setSuggesting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold capitalize">
          {section.replace(/_/g, " ")}
        </h3>
        {onAiSuggest && (
          <Button variant="secondary" size="sm" onClick={handleAiSuggest} disabled={suggesting}>
            {suggesting ? "Generating..." : "✨ AI Suggest"}
          </Button>
        )}
      </div>
      <div className="space-y-3">
        {fields.map((field) => (
          <div key={field}>
            <label className="block text-sm font-medium text-gray-700 mb-1 capitalize">
              {field.replace(/_/g, " ")}
            </label>
            <textarea
              value={data[field]}
              onChange={(e) => handleChange(field, e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              placeholder={`Enter ${field.replace(/_/g, " ")}...`}
            />
          </div>
        ))}
      </div>
      <Button onClick={handleSave}>Save Section</Button>
    </div>
  );
}
