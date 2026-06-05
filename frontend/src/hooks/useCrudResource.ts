import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ListParams, Paginated } from "@/types/crud";

export function useCrudResource<T extends { id: string }>(resource: string) {
  const path = `/v1/cadastros/${resource}`;
  const key = ["cadastros", resource];

  function useList(params: ListParams) {
    return useQuery<Paginated<T>>({
      queryKey: [...key, params],
      queryFn: () =>
        api
          .get<Paginated<T>>(path, {
            params: {
              search: params.search || undefined,
              limit: params.limit ?? 50,
              offset: params.offset ?? 0,
            },
          })
          .then((r) => r.data),
    });
  }

  function useItem(id: string | null) {
    return useQuery<T>({
      queryKey: [...key, "item", id],
      queryFn: () => api.get<T>(`${path}/${id}`).then((r) => r.data),
      enabled: id !== null,
    });
  }

  function useCreate() {
    const qc = useQueryClient();
    return useMutation({
      mutationFn: (data: Record<string, unknown>) =>
        api.post<T>(path, data).then((r) => r.data),
      onSuccess: () => qc.invalidateQueries({ queryKey: key }),
    });
  }

  function useUpdate() {
    const qc = useQueryClient();
    return useMutation({
      mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
        api.put<T>(`${path}/${id}`, data).then((r) => r.data),
      onSuccess: () => qc.invalidateQueries({ queryKey: key }),
    });
  }

  function useRemove() {
    const qc = useQueryClient();
    return useMutation({
      mutationFn: (id: string) => api.delete(`${path}/${id}`),
      onSuccess: () => qc.invalidateQueries({ queryKey: key }),
    });
  }

  return { useList, useItem, useCreate, useUpdate, useRemove };
}
