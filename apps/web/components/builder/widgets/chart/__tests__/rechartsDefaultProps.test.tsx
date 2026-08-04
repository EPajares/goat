import { render } from "@testing-library/react";
import { Cell, Pie, PieChart } from "recharts";
import { describe, expect, it } from "vitest";

/**
 * Recharts applies its own defaults with `{...defaultProps, ...props}` rather
 * than through React's defaultProps mechanism — the pattern it adopted for React
 * 19. The two are not equivalent: React substitutes a default when a prop is
 * `undefined`, a spread does not, it writes the `undefined` over the default.
 *
 * So `startAngle={cond ? 180 : undefined}` renders every sector at "M NaN,NaN".
 * These tests document that, so nobody reintroduces the conditional-undefined
 * shorthand in a chart widget.
 */

const DATA = [
  { grouped_value: "ja", operation_value: 53597150 },
  { grouped_value: "nein", operation_value: 8249262 },
];

const sectorPaths = (container: HTMLElement) =>
  [...container.querySelectorAll(".recharts-pie-sector path")].map((p) => p.getAttribute("d") ?? "");

const renderPie = (angles: Record<string, unknown>) =>
  render(
    <PieChart width={334} height={247}>
      <Pie
        data={DATA}
        dataKey="operation_value"
        nameKey="grouped_value"
        cx="50%"
        cy="50%"
        innerRadius="58%"
        isAnimationActive={false}
        {...angles}>
        {DATA.map((_, index) => (
          <Cell key={index} fill="#000" />
        ))}
      </Pie>
    </PieChart>
  );

describe("recharts angle props", () => {
  it("renders real coordinates when the angle props are omitted", () => {
    const paths = sectorPaths(renderPie({}).container);
    expect(paths).toHaveLength(2);
    for (const d of paths) {
      expect(d).not.toContain("NaN");
      expect(d).toMatch(/^M [\d.]+,[\d.]+/);
    }
  });

  it("renders real coordinates for explicit numeric angles", () => {
    const paths = sectorPaths(renderPie({ startAngle: 180, endAngle: 0 }).container);
    for (const d of paths) expect(d).not.toContain("NaN");
  });

  it("produces NaN geometry when an angle is passed as explicit undefined", () => {
    // The failure this guards against. If a future recharts makes this safe,
    // this test flips and the conditional spreads in the widgets can be relaxed.
    const paths = sectorPaths(renderPie({ startAngle: undefined, endAngle: undefined }).container);
    expect(paths.every((d) => d.includes("NaN"))).toBe(true);
  });
});
