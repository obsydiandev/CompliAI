export default function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[
          { name: "GitHub", desc: "Connect your GitHub repositories" },
          { name: "GitLab", desc: "Connect your GitLab projects" },
          { name: "MLflow", desc: "Import experiment metrics" },
          { name: "Weights & Biases", desc: "Import training runs" },
        ].map((integration) => (
          <div
            key={integration.name}
            className="bg-white p-6 rounded-xl shadow-sm border border-gray-200"
          >
            <h2 className="text-lg font-semibold text-gray-900">{integration.name}</h2>
            <p className="text-gray-500 mt-1 text-sm">{integration.desc}</p>
            <button className="mt-4 px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
              Configure
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
