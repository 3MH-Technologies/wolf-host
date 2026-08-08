export function WolfLogo({ className = "w-8 h-8" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M24 4L8 14V26C8 34.8 14.8 42.4 24 44C33.2 42.4 40 34.8 40 26V14L24 4Z"
        stroke="url(#wolfGradient)"
        strokeWidth="2"
        fill="rgba(245,148,60,0.05)"
      />
      <circle cx="17" cy="22" r="2.2" fill="#ffb454" className="animate-pulse-glow" />
      <circle cx="31" cy="22" r="2.2" fill="#ffb454" className="animate-pulse-glow" />
      <path d="M24 26L20 32H28L24 26Z" fill="#f5943c" opacity="0.8" />
      <defs>
        <linearGradient id="wolfGradient" x1="8" y1="4" x2="40" y2="44" gradientUnits="userSpaceOnUse">
          <stop stopColor="#ffb454" />
          <stop offset="1" stopColor="#d9772a" />
        </linearGradient>
      </defs>
    </svg>
  );
}
