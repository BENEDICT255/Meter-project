"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Droplet } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button, buttonVariants } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useMeters } from "@/hooks/use-meters";
import { useInitiateTransaction } from "@/hooks/use-transactions";
import { getApiErrorMessage } from "@/lib/api";

const schema = z.object({
  meter_id: z.string().uuid("Pick a meter"),
  amount: z
    .string()
    .regex(/^\d+$/, "Amount must be a positive integer")
    .refine((v) => parseInt(v, 10) >= 1, "Amount must be at least 1"),
});

type Values = z.infer<typeof schema>;

export default function BuyPage() {
  const router = useRouter();
  const meters = useMeters();
  const initiate = useInitiateTransaction();

  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { meter_id: "", amount: "" },
  });

  const onSubmit = (values: Values) => {
    initiate.mutate(values, {
      onSuccess: (txn) => {
        router.push(`/transactions/${txn.id}`);
      },
      onError: (err) => {
        form.setError("root", { message: getApiErrorMessage(err) });
      },
    });
  };

  if (meters.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading...</p>;
  }

  if (meters.data && meters.data.length === 0) {
    return (
      <div className="mx-auto max-w-md py-12 text-center">
        <div className="mx-auto flex size-14 items-center justify-center rounded-full bg-primary/10">
          <Droplet className="size-7 text-primary" />
        </div>
        <h2 className="mt-6 text-2xl font-semibold tracking-tight">Add your first meter</h2>
        <p className="mt-2 text-muted-foreground">
          You need a registered meter before you can buy a token.
        </p>
        <Link href="/meters" className={buttonVariants({ size: "lg", className: "mt-6 h-12 px-6 text-base" })}>
          Add a meter
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Buy a token</h1>
        <p className="text-muted-foreground">Pick a meter and enter the amount in shillings.</p>
      </div>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="mt-8 space-y-6">
          <FormField
            control={form.control}
            name="meter_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Meter</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder="Pick a meter" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {meters.data?.map((m) => (
                      <SelectItem key={m.id} value={m.id}>
                        <span className="font-mono">{m.meter_number}</span>
                        {m.label ? <span className="ml-2 text-muted-foreground">— {m.label}</span> : null}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="amount"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Amount</FormLabel>
                <FormControl>
                  <div className="relative">
                    <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-sm font-medium text-muted-foreground">
                      TZS
                    </span>
                    <Input
                      inputMode="numeric"
                      placeholder="5000"
                      className="h-14 pl-14 text-2xl font-semibold tracking-tight"
                      {...field}
                    />
                  </div>
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
          <Button
            type="submit"
            size="lg"
            disabled={initiate.isPending}
            className="h-12 w-full text-base"
          >
            {initiate.isPending ? "Generating control number..." : "Continue"}
          </Button>
        </form>
      </Form>
    </div>
  );
}
