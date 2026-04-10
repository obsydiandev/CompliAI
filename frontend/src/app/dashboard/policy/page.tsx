export default function PolicyPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Policy Engine</h1>
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold mb-4">Policy Rules</h2>
        <p className="text-gray-500">Configure automated compliance checks for your AI systems.</p>
        <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
          + Add Rule
        </button>
      </div>
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold mb-4">Built-in Rule Types</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {["accuracy_threshold", "bias_check", "data_quality", "model_drift", "compliance_completeness"].map(
            (rule) => (
              <div key={rule} className="p-3 bg-gray-50 rounded-lg">
                <span className="font-mono text-sm text-blue-700">{rule}</span>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
