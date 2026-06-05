import { Link } from "react-router-dom";
import { CADASTROS } from "@/config/cadastros";

export function CadastrosIndex() {
  return (
    <div className="p-6">
      <h2 className="mb-4 text-2xl font-bold">Cadastros</h2>
      <ul className="grid grid-cols-2 gap-3 md:grid-cols-3">
        {Object.values(CADASTROS).map((c) => (
          <li key={c.resource}>
            <Link
              to={`/cadastros/${c.resource}`}
              className="block rounded border border-gray-200 p-4 hover:bg-gray-50"
            >
              {c.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
