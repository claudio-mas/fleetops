import { Outlet, useLocation } from "react-router-dom";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { getCadastro } from "@/config/cadastros";

function useRouteTitle(): string {
  const { pathname } = useLocation();
  if (pathname === "/dashboard") return "Início";
  if (pathname.startsWith("/cadastros/")) {
    const slug = pathname.split("/")[2];
    return getCadastro(slug)?.label ?? "Cadastro";
  }
  if (pathname.startsWith("/configuracoes")) return "Segurança";
  if (pathname.startsWith("/mfa-setup")) return "Autenticação de Dois Fatores";
  return "FleetOps";
}

export function AppLayout() {
  const title = useRouteTitle();
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <h1 className="text-sm font-semibold">{title}</h1>
        </header>
        <div className="flex-1 p-6">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
