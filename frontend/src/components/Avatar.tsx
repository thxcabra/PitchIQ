import { useState } from "react";

function initials(name: string) {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[parts.length - 1]?.[0] ?? "")).toUpperCase();
}

// Player portrait with graceful fallback to initials when the photo is missing / 404s.
export default function Avatar({
  src, name, size = 44, className = "",
}: { src: string | null | undefined; name: string; size?: number; className?: string }) {
  const [failed, setFailed] = useState(false);
  const dim = { width: size, height: size } as const;
  if (!src || failed) {
    return (
      <span
        style={dim}
        className={`shrink-0 grid place-items-center rounded-full bg-pitch-card2 border border-pitch-line
                    text-pitch-sub font-semibold ${className}`}
      >
        <span style={{ fontSize: size * 0.36 }}>{initials(name)}</span>
      </span>
    );
  }
  return (
    <img
      src={src} alt="" loading="lazy" style={dim} onError={() => setFailed(true)}
      className={`shrink-0 rounded-full object-cover bg-pitch-card2 border border-pitch-line ${className}`}
    />
  );
}

// Small crest / flag image that simply disappears if it fails to load.
export function Logo({ src, size = 20, className = "" }: { src: string | null | undefined; size?: number; className?: string }) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) return null;
  return (
    <img src={src} alt="" loading="lazy" width={size} height={size} onError={() => setFailed(true)}
         className={`shrink-0 object-contain ${className}`} />
  );
}
