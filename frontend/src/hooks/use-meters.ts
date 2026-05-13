"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Meter } from "@/types/api";

const KEY = ["meters"] as const;

export function useMeters() {
  return useQuery({
    queryKey: KEY,
    queryFn: async () => {
      const resp = await api.get<Meter[]>("/meters/");
      return resp.data;
    },
  });
}

interface CreateInput {
  meter_number: string;
  label?: string;
}

export function useCreateMeter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateInput) => {
      const resp = await api.post<Meter>("/meters/", input);
      return resp.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEY });
    },
  });
}

export function useDeleteMeter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/meters/${id}/`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEY });
    },
  });
}
