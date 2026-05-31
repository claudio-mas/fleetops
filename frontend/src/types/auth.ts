export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

export interface MFALoginResponse {
  mfa_required?: boolean;
  mfa_challenge_token?: string;
  access_token?: string;
  refresh_token?: string;
  token_type?: string;
}

export interface UserRead {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  mfa_enabled: boolean;
  email_verified_at: string | null;
  created_at: string;
}

export interface TenantRegistrationRequest {
  razao_social: string;
  cnpj: string;
  admin_email: string;
  admin_password: string;
  admin_full_name: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}
