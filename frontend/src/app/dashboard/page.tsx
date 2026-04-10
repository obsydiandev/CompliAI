export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-sm font-medium text-gray-500">AI Systems</h2>
          <p className="mt-2 text-3xl font-bold text-gray-900">—</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-sm font-medium text-gray-500">Avg. Completeness</h2>
          <p className="mt-2 text-3xl font-bold text-gray-900">—%</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-sm font-medium text-gray-500">Policy Rules</h2>
          <p className="mt-2 text-3xl font-bold text-gray-900">—</p>
        </div>
      </div>
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Getting Started</h2>
        <ol className="list-decimal list-inside space-y-2 text-gray-600">
          <li>Create your first AI system documentation</li>
          <li>Fill in the 9 Annex IV sections</li>
          <li>Use the AI assistant to identify gaps</li>
          <li>Export your compliance documentation</li>
        </ol>
      </div>
    </div>
  );
}
