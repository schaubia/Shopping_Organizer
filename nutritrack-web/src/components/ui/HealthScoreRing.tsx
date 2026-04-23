interface Props { score: number; size?: number; }

export default function HealthScoreRing({ score, size = 80 }: Props) {
  const radius      = (size / 2) - 8;
  const circumference = 2 * Math.PI * radius;
  const filled      = (score / 10) * circumference;
  const color       = score >= 7 ? "#16a34a" : score >= 4 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={radius}
          fill="none" stroke="#e5e7eb" strokeWidth="8" />
        <circle cx={size/2} cy={size/2} r={radius}
          fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - filled}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease" }} />
        <text x={size/2} y={size/2 + 5}
          textAnchor="middle" style={{ transform: "rotate(90deg)", transformOrigin: "center" }}
          fill={color} fontSize="18" fontWeight="700">
          {score}
        </text>
      </svg>
      <span className="text-xs text-gray-500 font-medium">Health score</span>
    </div>
  );
}
