export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface BaseRecord {
  id: string;
  tenant_id: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ListParams {
  search?: string;
  limit?: number;
  offset?: number;
}
