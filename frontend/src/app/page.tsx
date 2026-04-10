import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center space-y-6 p-8 max-w-2xl">
        <h1 className="text-5xl font-bold text-gray-900">CompliAI</h1>
        <p className="text-xl text-gray-600">
          EU AI Act Annex IV compliance documentation platform
        </p>
        <p className="text-gray-500">
          Build, maintain, and export complete technical documentation for your AI systems.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/dashboard"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Go to Dashboard
          </Link>
          <Link
            href="/login"
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
          >
            Sign In
          </Link>
        </div>
      </div>
    </main>
  );
}
