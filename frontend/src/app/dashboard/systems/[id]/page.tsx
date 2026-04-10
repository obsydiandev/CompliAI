import Link from "next/link";

interface Props {
  params: { id: string };
}

export default function SystemDetailPage({ params }: Props) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/systems" className="text-blue-600 hover:underline text-sm">
          ← Back to Systems
        </Link>
      </div>
      <h1 className="text-2xl font-bold text-gray-900">System: {params.id}</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">Annex IV Documentation</h2>
          <Link
            href={`/dashboard/systems/${params.id}/annex-iv`}
            className="block w-full text-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Open Documentation
          </Link>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">Completeness</h2>
          <p className="text-4xl font-bold text-gray-900">—%</p>
        </div>
      </div>
    </div>
  );
}
