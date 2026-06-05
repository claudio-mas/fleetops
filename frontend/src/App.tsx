import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Dashboard } from "@/pages/Dashboard";
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import VerifyEmail from "@/pages/VerifyEmail";
import MFASetup from "@/pages/MFASetup";
import { CadastrosIndex } from "@/pages/cadastros/CadastrosIndex";
import { CadastroPage } from "@/pages/cadastros/CadastroPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/mfa-setup" element={<MFASetup />} />
        <Route path="/cadastros" element={<CadastrosIndex />} />
        <Route path="/cadastros/:resource" element={<CadastroPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
