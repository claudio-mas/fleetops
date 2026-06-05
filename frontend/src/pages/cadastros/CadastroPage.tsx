import { useParams } from "react-router-dom";
import { CrudListPage } from "@/components/crud/CrudListPage";
import { getCadastro } from "@/config/cadastros";

export function CadastroPage() {
  const { resource } = useParams<{ resource: string }>();
  const config = resource ? getCadastro(resource) : undefined;
  if (!config) {
    return <div className="p-6 text-gray-600">Cadastro não encontrado.</div>;
  }
  return <CrudListPage config={config} />;
}
