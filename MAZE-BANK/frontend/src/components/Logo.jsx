export default function Logo({ size = 24 }) {
  const mark = Math.round(size * 1.65)
  return (
    <span className="logo">
      <span className="mark" style={{ width: mark, height: mark }}>
        <svg viewBox="0 0 46 46" width={mark} height={mark} aria-hidden="true">
          <g fill="none" stroke="#fff" strokeWidth="4" strokeLinecap="square">
            <path d="M11 14 H33 V33 H17 V22 H28 V28" />
          </g>
        </svg>
      </span>
      <span className="word" style={{ fontSize: size }}>
        <span className="m">MAZE</span><span className="b">BANK</span>
      </span>
    </span>
  )
}
