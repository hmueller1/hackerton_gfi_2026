import { Metadata } from "next";
import Dashboard from "@/components/beruf/Dashboard";

export const metadata: Metadata = { title: "Dashboard" };

export default function HomePage() {
  return <Dashboard />;
}
