"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Droplet } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button, buttonVariants } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useMe } from "@/hooks/use-auth";
import { useMeters } from "@/hooks/use-meters";
import { useInitiateTransaction } from "@/hooks/use-transactions";
import { getApiErrorMessage } from "@/lib/api";

const PHONE_REGEX = /^(?:\+?255|0)\d{9}$/;

const schema = z.object({
  meter_id: z.string().uuid("Pick a meter"),
  amount: z
    .string()
    .regex(/^\d+$/, "Amount must be a positive integer")
    .refine((v) => parseInt(v, 10) >= 1, "Amount must be at least 1"),
  phone_number: z
    .string()
    .regex(PHONE_REGEX, "Enter a Tanzanian number (e.g. 0712345678 or +255712345678)"),
});

type Values = z.infer<typeof schema>;

export default function BuyPage() {
  const router = useRouter();
  const meters = useMeters();
  const me = useMe();
  const initiate = useInitiateTransaction();

  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { meter_id: "", amount: "", phone_number: "" },
  });

  useEffect(() => {
    if (me.data?.phone_number && !form.getValues("phone_number")) {
      form.setValue("phone_number", me.data.phone_number);
    }
  }, [me.data?.phone_number, form]);

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
        <p className="text-muted-foreground">
          Pick a meter, enter the amount, and confirm the phone that will receive the payment popup.
        </p>
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
          <FormField
            control={form.control}
            name="phone_number"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Phone for payment</FormLabel>
                <FormControl>
                  <Input
                    inputMode="tel"
                    placeholder="+255712345678"
                    className="h-12"
                    {...field}
                  />
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
            {initiate.isPending ? "Starting payment..." : "Pay"}
          </Button>
        </form>
      </Form>
    </div>
  );
}
