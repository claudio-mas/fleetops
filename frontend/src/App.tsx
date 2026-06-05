import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Home } from "@/pages/Home";
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import VerifyEmail from "@/pages/VerifyEmail";
import MFASetup from "@/pages/MFASetup";
import { SecuritySettings } from "@/pages/settings/SecuritySettings";
import { CadastroPage } from "@/pages/cadastros/CadastroPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Home />} />
          <Route path="/mfa-setup" element={<MFASetup />} />
          <Route path="/cadastros/:resource" element={<CadastroPage />} />
          <Route path="/configuracoes/seguranca" element={<SecuritySettings />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
