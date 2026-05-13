"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Droplets } from "lucide-react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useRegister } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/api";

const schema = z.object({
  phone_number: z.string().min(8, "Phone number is required"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type Values = z.infer<typeof schema>;

export default function RegisterPage() {
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { phone_number: "", password: "" },
  });
  const register = useRegister();

  const onSubmit = (values: Values) => {
    register.mutate(values, {
      onError: (err) => {
        form.setError("root", { message: getApiErrorMessage(err) });
      },
    });
  };

  return (
    <main className="flex min-h-screen flex-col bg-white">
      <header className="px-8 py-6">
        <div className="flex items-center gap-2 text-foreground">
          <Droplets className="size-6 text-primary" />
          <span className="text-lg font-semibold tracking-tight">Daraja Water</span>
        </div>
      </header>
      <div className="flex flex-1 items-center justify-center px-6 pb-16">
        <div className="w-full max-w-md space-y-8">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">Create an account</h1>
            <p className="text-muted-foreground">Top up your water meter in seconds.</p>
          </div>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="phone_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Phone number</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="+255700000000"
                        className="h-12 text-base"
                        inputMode="tel"
                        autoComplete="tel"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        className="h-12 text-base"
                        autoComplete="new-password"
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
                disabled={register.isPending}
                className="h-12 w-full text-base"
              >
                {register.isPending ? "Creating account..." : "Create account"}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link href="/login" className="font-medium text-primary hover:underline">
                  Sign in
                </Link>
              </p>
            </form>
          </Form>
        </div>
      </div>
    </main>
  );
}
