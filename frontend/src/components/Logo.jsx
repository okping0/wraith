export default function Logo({ size = 28 }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <svg width={size} height={size} viewBox="0 0 60 60">
        <path
          d="M12 30 Q12 8 30 8 Q48 8 48 30 L48 52 Q42 46 36 52 Q30 46 24 52 Q18 46 12 52 Z"
          fill="#b9a7ff"
        />
        <circle cx="23" cy="29" r="4" fill="#1a1726" />
        <circle cx="37" cy="29" r="4" fill="#1a1726" />
      </svg>
      <span style={{ fontWeight: 700, letterSpacing: 2 }}>WRAITH</span>
    </div>
  );
}