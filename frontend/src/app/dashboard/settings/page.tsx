export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 space-y-4">
        <h2 className="text-lg font-semibold">Organization</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Organization Name</label>
          <input
            type="text"
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full max-w-md"
            placeholder="My Organization"
          />
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
          Save Changes
        </button>
      </div>
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold mb-4">Billing Plan</h2>
        <div className="grid grid-cols-3 gap-4">
          {[
            { name: "Starter", price: "$49/mo" },
            { name: "Professional", price: "$149/mo" },
            { name: "Enterprise", price: "Custom" },
          ].map((plan) => (
            <div key={plan.name} className="p-4 border border-gray-200 rounded-lg text-center">
              <p className="font-semibold">{plan.name}</p>
              <p className="text-gray-500 text-sm">{plan.price}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
