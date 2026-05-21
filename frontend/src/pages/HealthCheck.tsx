import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";

interface HealthResponse {
  status: string;
}

export default function HealthCheck(): JSX.Element {
  const { data, isPending, isError, error } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await api.get<HealthResponse>("/health");
      return res.data;
    },
  });

  if (isPending) return <p>Checking backend…</p>;
  if (isError) return <p className="text-red-600">Error: {(error as Error).message}</p>;

  return <p>Backend status: {data.status}</p>;
}
