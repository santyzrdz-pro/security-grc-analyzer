import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function classForSeverity(value?: string): string {
  switch (value) {
    case "Critical":
      return "bg-critical/15 text-critical border-critical/30";
    case "High":
      return "bg-danger/15 text-danger border-danger/30";
    case "Medium":
      return "bg-warning/15 text-warning border-warning/30";
    case "Low":
      return "bg-success/15 text-success border-success/30";
    default:
      return "bg-surface-2 text-muted border-border";
  }
}

export function classForStatus(value?: string): string {
  switch (value) {
    case "Open":
    case "Not Started":
      return "bg-danger/15 text-danger border-danger/30";
    case "In Progress":
      return "bg-warning/15 text-warning border-warning/30";
    case "Blocked":
      return "bg-critical/15 text-critical border-critical/30";
    case "Resolved":
    case "Completed":
    case "Implemented":
      return "bg-success/15 text-success border-success/30";
    case "Accepted Risk":
      return "bg-primary/15 text-primary border-primary/30";
    default:
      return "bg-surface-2 text-muted border-border";
  }
}

export function gradeColor(grade?: string): string {
  switch (grade) {
    case "A":
      return "text-success";
    case "B":
      return "text-success";
    case "C":
      return "text-warning";
    case "D":
      return "text-danger";
    default:
      return "text-critical";
  }
}
