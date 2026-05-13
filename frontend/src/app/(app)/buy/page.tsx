"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
      <Card>
        <CardHeader>
          <CardTitle>No meters yet</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p>You need to add a meter before you can buy a token.</p>
          <Button asChild>
            <Link href="/meters">Add a meter first</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="max-w-md">
      <CardHeader>
        <CardTitle>Buy a token</CardTitle>
      </CardHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="meter_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Meter</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Pick a meter" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {meters.data?.map((m) => (
                        <SelectItem key={m.id} value={m.id}>
                          {m.meter_number}
                          {m.label ? ` — ${m.label}` : ""}
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
                  <FormLabel>Amount (TZS)</FormLabel>
                  <FormControl>
                    <Input inputMode="numeric" placeholder="5000" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {form.formState.errors.root && (
              <p className="text-sm text-destructive">{form.formState.errors.root.message}</p>
            )}
            <Button type="submit" disabled={initiate.isPending} className="w-full">
              {initiate.isPending ? "Initiating..." : "Pay"}
            </Button>
          </CardContent>
        </form>
      </Form>
    </Card>
  );
}
