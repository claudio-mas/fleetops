import { LoginForm } from "@/components/auth/LoginForm";
import { Link } from "react-router-dom";

export function Login() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h1 className="text-center text-3xl font-bold tracking-tight text-gray-900">
            FleetOps
          </h1>
          <h2 className="mt-2 text-center text-lg text-gray-600">
            Acesse sua conta
          </h2>
        </div>
        <div className="rounded-lg border bg-white p-8 shadow-sm">
          <LoginForm />
          <p className="mt-6 text-center text-sm text-gray-500">
            Sem conta?{" "}
            <Link to="/register" className="font-medium text-indigo-600 hover:text-indigo-500">
              Criar conta grátis
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
