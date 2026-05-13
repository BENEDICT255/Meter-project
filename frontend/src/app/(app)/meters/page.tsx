"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Gauge, Trash2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useCreateMeter, useDeleteMeter, useMeters } from "@/hooks/use-meters";
import { getApiErrorMessage } from "@/lib/api";

const schema = z.object({
  meter_number: z
    .string()
    .regex(/^\d{10,14}$/, "Meter number must be 10–14 digits"),
  label: z.string().optional(),
});

type Values = z.infer<typeof schema>;

export default function MetersPage() {
  const meters = useMeters();
  const create = useCreateMeter();
  const remove = useDeleteMeter();

  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { meter_number: "", label: "" },
  });

  const onSubmit = (values: Values) => {
    create.mutate(values, {
      onSuccess: () => {
        toast.success("Meter added");
        form.reset();
      },
      onError: (err) => {
        form.setError("root", { message: getApiErrorMessage(err) });
      },
    });
  };

  return (
    <div className="mx-auto max-w-2xl space-y-10">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Meters</h1>
        <p className="text-muted-foreground">Register the water meters you want to top up.</p>
      </div>

      <section className="rounded-xl border bg-white p-6">
        <h2 className="text-lg font-semibold">Add a meter</h2>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="mt-4 space-y-4">
            <FormField
              control={form.control}
              name="meter_number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Meter number</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="0100000001"
                      className="h-11 font-mono"
                      inputMode="numeric"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="label"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Label (optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="Home" className="h-11" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {form.formState.errors.root && (
              <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                {form.formState.errors.root.message}
              </div>
            )}
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Adding..." : "Add meter"}
            </Button>
          </form>
        </Form>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Your meters</h2>
        <div className="mt-4 overflow-hidden rounded-xl border bg-white">
          {meters.isLoading && (
            <p className="px-6 py-12 text-center text-sm text-muted-foreground">Loading...</p>
          )}
          {meters.data && meters.data.length === 0 && (
            <p className="px-6 py-12 text-center text-sm text-muted-foreground">
              No meters yet.
            </p>
          )}
          {meters.data && meters.data.length > 0 && (
            <ul className="divide-y">
              {meters.data.map((m) => (
                <li key={m.id} className="flex items-center justify-between px-5 py-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/10">
                      <Gauge className="size-4 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-mono text-sm">{m.meter_number}</p>
                      {m.label && (
                        <p className="truncate text-xs text-muted-foreground">{m.label}</p>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Delete meter ${m.meter_number}`}
                    disabled={remove.isPending}
                    onClick={() => {
                      if (confirm(`Delete meter ${m.meter_number}?`)) {
                        remove.mutate(m.id);
                      }
                    }}
                  >
                    <Trash2 className="size-4 text-muted-foreground" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
