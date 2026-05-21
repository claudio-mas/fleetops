import HealthCheck from "./pages/HealthCheck";

export default function App(): JSX.Element {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-slate-900">FleetOps</h1>
        <p className="text-slate-600">Foundation skeleton ready.</p>
        <div className="text-slate-700 text-sm">
          <HealthCheck />
        </div>
      </div>
    </div>
  );
}
