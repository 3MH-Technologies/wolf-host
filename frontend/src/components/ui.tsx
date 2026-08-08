import { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

export function Button({
  children,
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" | "ghost"; children: ReactNode }) {
  const variants = {
    primary: "bg-gradient-to-b from-ember-400 to-ember-600 text-slate-950 font-semibold hover:shadow-glow",
    secondary: "bg-slate-800 text-slate-200 border border-slate-700 hover:bg-slate-700",
    danger: "bg-signal-red/10 text-signal-red border border-signal-red/30 hover:bg-signal-red/20",
    ghost: "text-slate-400 hover:text-slate-200 hover:bg-slate-800",
  };
  return (
    <button
      className={clsx(
        "px-4 py-2 rounded-lg text-sm transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={clsx(
        "w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200",
        "placeholder:text-slate-600 focus:outline-none focus:border-ember-500 focus:ring-1 focus:ring-ember-500/40",
        "transition-colors",
        className
      )}
      {...props}
    />
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx("card-surface rounded-2xl p-6", className)}>{children}</div>;
}

export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    running: "text-signal-green border-signal-green/30 bg-signal-green/10",
    stopped: "text-slate-400 border-slate-600 bg-slate-800",
    crashed: "text-signal-red border-signal-red/30 bg-signal-red/10",
    error: "text-signal-red border-signal-red/30 bg-signal-red/10",
    installing: "text-ember-400 border-ember-500/30 bg-ember-500/10",
    created: "text-signal-blue border-signal-blue/30 bg-signal-blue/10",
    deleting: "text-slate-400 border-slate-600 bg-slate-800",
  };
  return (
    <span className={clsx("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border font-medium", colors[status] || colors.stopped)}>
      <span className="w-1.5 h-1.5 rounded-full status-dot bg-current" />
      {status}
    </span>
  );
}
