"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";
import { Spinner } from "@/components/ui/primitives";

export default function HomePage() {
  const router = useRouter();
  useEffect(() => {
    router.replace(getToken() ? "/dashboard" : "/login");
  }, [router]);
  return (
    <div className="flex h-screen items-center justify-center">
      <Spinner className="h-8 w-8" />
    </div>
  );
}
