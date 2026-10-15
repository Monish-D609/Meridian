import React from 'react';

export interface CategoryData {
  category: string;
  candidateScore: number; // 0 to 1
  baselineScore: number;  // 0 to 1
}

interface RadarChartProps {
  data: CategoryData[];
  candidateName?: string;
  baselineName?: string;
}

export const RadarChart: React.FC<RadarChartProps> = ({
  data,
  candidateName = 'Candidate Model',
  baselineName = 'Baseline Median',
}) => {
  if (!data || data.length === 0) return null;

  const width = 400;
  const height = 320;
  const cx = 190;
  const cy = 160;
  const maxRadius = 110;

  const numAxes = data.length;
  const angleStep = (2 * Math.PI) / numAxes;
  const startAngle = -Math.PI / 2; // top

  // Rings at 25%, 50%, 75%, 100%
  const ringLevels = [0.25, 0.5, 0.75, 1.0];

  const getPoints = (level: number | ((d: CategoryData) => number)) => {
    return data
      .map((d, i) => {
        const val = typeof level === 'function' ? level(d) : level;
        const r = maxRadius * Math.max(0.05, Math.min(1.0, val));
        const angle = startAngle + i * angleStep;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  };

  const candidatePoints = getPoints((d) => d.candidateScore);
  const baselinePoints = getPoints((d) => d.baselineScore);

  return (
    <div style={{ width: '100%' }}>
      <svg
        className="chart"
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: 'auto', display: 'block' }}
      >
        {/* Concentric rings */}
        {ringLevels.map((lvl, idx) => (
          <polygon key={idx} className="ring" points={getPoints(lvl)} />
        ))}

        {/* Spokes */}
        <g className="spoke">
          {data.map((_, i) => {
            const angle = startAngle + i * angleStep;
            const x = cx + maxRadius * Math.cos(angle);
            const y = cy + maxRadius * Math.sin(angle);
            return <line key={i} x1={cx} y1={cy} x2={x.toFixed(1)} y2={y.toFixed(1)} />;
          })}
        </g>

        {/* Baseline polygon */}
        <polygon className="base" points={baselinePoints} />

        {/* Candidate polygon */}
        <polygon className="cand" points={candidatePoints} />

        {/* Labels */}
        {data.map((d, i) => {
          const angle = startAngle + i * angleStep;
          const labelRadius = maxRadius + 22;
          const x = cx + labelRadius * Math.cos(angle);
          const y = cy + labelRadius * Math.sin(angle);

          let anchor: 'middle' | 'start' | 'end' = 'middle';
          if (Math.cos(angle) > 0.3) anchor = 'start';
          else if (Math.cos(angle) < -0.3) anchor = 'end';

          return (
            <text key={i} x={x.toFixed(1)} y={(y + 4).toFixed(1)} textAnchor={anchor}>
              {d.category}
            </text>
          );
        })}
      </svg>

      <div className="legend-row">
        <span>
          <i className="sw" style={{ background: 'var(--accent)' }} />
          {candidateName}
        </span>
        <span>
          <i className="sw" style={{ border: '1.5px dashed var(--ink-3)' }} />
          {baselineName}
        </span>
      </div>
    </div>
  );
};
