"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Add a meter</CardTitle>
        </CardHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="meter_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Meter number</FormLabel>
                    <FormControl>
                      <Input placeholder="0100000001" {...field} />
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
                      <Input placeholder="Home" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {form.formState.errors.root && (
                <p className="text-sm text-destructive">{form.formState.errors.root.message}</p>
              )}
              <Button type="submit" disabled={create.isPending}>
                {create.isPending ? "Adding..." : "Add meter"}
              </Button>
            </CardContent>
          </form>
        </Form>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your meters</CardTitle>
        </CardHeader>
        <CardContent>
          {meters.isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
          {meters.data && meters.data.length === 0 && (
            <p className="text-sm text-muted-foreground">No meters yet.</p>
          )}
          {meters.data && meters.data.length > 0 && (
            <ul className="divide-y">
              {meters.data.map((m) => (
                <li key={m.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-mono">{m.meter_number}</p>
                    {m.label && <p className="text-sm text-muted-foreground">{m.label}</p>}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={remove.isPending}
                    onClick={() => {
                      if (confirm(`Delete meter ${m.meter_number}?`)) {
                        remove.mutate(m.id);
                      }
                    }}
                  >
                    Delete
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
