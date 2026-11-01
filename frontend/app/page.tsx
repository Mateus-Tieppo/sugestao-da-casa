"use client";

import { useEffect } from "react";
import { aquecer } from "@/lib/api";

// Página provisória: acorda o backend e mostra o título. As telas vêm nas próximas tarefas.
export default function Home() {
  useEffect(() => {
    aquecer();
  }, []);

  return (
    <main className="flex flex-1 items-center justify-center px-4">
      <h1 className="font-titulo text-4xl text-tomate">Sugestão da Casa</h1>
    </main>
  );
}
