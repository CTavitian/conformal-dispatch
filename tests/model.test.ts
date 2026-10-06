import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { backtest, calibrateQuantile, rawRisk, scoreAsset } from "../src/model.js";
import type { AssetFeatures } from "../src/types.js";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");

describe("conformal-dispatch", () => {
  it("rawRisk is in (0,1) and rises with wear signals", () => {
    const low: AssetFeatures = {
      id: "a",
      runtime_hours: 800,
      alarm_rate_7d: 0.2,
      days_since_pm: 20,
      criticality: 1,
    };
    const high: AssetFeatures = {
      id: "b",
      runtime_hours: 11000,
      alarm_rate_7d: 7,
      days_since_pm: 350,
      criticality: 3,
    };
    expect(rawRisk(low)).toBeGreaterThan(0);
    expect(rawRisk(low)).toBeLessThan(1);
    expect(rawRisk(high)).toBeGreaterThan(rawRisk(low));
  });

  it("empirical coverage on holdout is near 1-alpha (loose band)", async () => {
    const data = JSON.parse(
      await readFile(path.join(root, "fixtures/assets.json"), "utf8"),
    ) as { calibration: AssetFeatures[]; holdout: AssetFeatures[] };
    const alpha = 0.1;
    const { summary } = backtest(data.calibration, data.holdout, alpha);
    // Finite-sample conformal: allow generous slack on synthetic fixtures
    expect(summary.empirical_coverage).toBeGreaterThanOrEqual(0.7);
    expect(summary.target_coverage).toBeCloseTo(0.9);
  });

  it("criticality-3 never auto-commits", () => {
    const a: AssetFeatures = {
      id: "c3",
      runtime_hours: 500,
      alarm_rate_7d: 0.1,
      days_since_pm: 10,
      criticality: 3,
      failed: false,
    };
    const q = 0.05;
    const r = scoreAsset(a, q, 0.1);
    expect(r.decision).not.toBe("commit");
  });

  it("wide intervals map to hold", () => {
    const a: AssetFeatures = {
      id: "w",
      runtime_hours: 5000,
      alarm_rate_7d: 3,
      days_since_pm: 180,
      criticality: 2,
    };
    const r = scoreAsset(a, 0.6, 0.1);
    expect(r.decision).toBe("hold");
    expect(r.prediction_set.length).toBeGreaterThanOrEqual(1);
  });

  it("calibrateQuantile is positive", async () => {
    const data = JSON.parse(
      await readFile(path.join(root, "fixtures/assets.json"), "utf8"),
    ) as { calibration: AssetFeatures[] };
    expect(calibrateQuantile(data.calibration, 0.1)).toBeGreaterThan(0);
  });
});
