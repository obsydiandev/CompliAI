import Link from "next/link";

interface Props {
  params: { id: string };
}

const SECTIONS = [
  "general_information",
  "intended_purpose",
  "technical_specifications",
  "training_data",
  "testing_and_validation",
  "human_oversight",
  "cybersecurity",
  "transparency",
  "post_market_monitoring",
];

export default function AnnexIVPage({ params }: Props) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          href={`/dashboard/systems/${params.id}`}
          className="text-blue-600 hover:underline text-sm"
        >
          ← Back to System
        </Link>
      </div>
      <h1 className="text-2xl font-bold text-gray-900">Annex IV Documentation</h1>
      <div className="space-y-4">
        {SECTIONS.map((section) => (
          <div
            key={section}
            className="bg-white p-6 rounded-xl shadow-sm border border-gray-200"
          >
            <h2 className="text-lg font-semibold text-gray-900 capitalize">
              {section.replace(/_/g, " ")}
            </h2>
            <div className="mt-2 h-2 bg-gray-200 rounded-full">
              <div className="h-2 bg-blue-500 rounded-full w-0" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
