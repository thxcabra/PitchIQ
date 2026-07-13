import Icon from "./Icon";

// Small info glyph with a hover/focus tooltip. Keyboard-accessible (tabbable + focus-visible).
export default function InfoTip({ text, size = 15 }: { text: string; size?: number }) {
  return (
    <span className="group relative inline-flex align-middle">
      <button type="button" aria-label="What does this mean?"
              className="text-pitch-muted hover:text-pitch-accent transition-colors">
        <Icon name="info" size={size} />
      </button>
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-30 mt-2 w-64 -translate-x-1/2
                   rounded-lg border border-pitch-line2 bg-pitch-bg2 px-3 py-2 text-left text-xs
                   font-normal leading-relaxed text-pitch-sub shadow-lift opacity-0
                   transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100"
      >
        {text}
      </span>
    </span>
  );
}
