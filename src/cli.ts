#!/usr/bin/env node
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { backtest, calibrateQuantile, scoreAsset } from "./model.js";
import type { AssetFeatures } from "./types.js";

function usage(): never {
  console.log(`Usage: conformal-dispatch --fixtures <assets.json> [--alpha 0.1] [--out report.json]`);
  process.exit(1);
}

function argValue(args: string[], flag: string): string | undefined {
  const i = args.indexOf(flag);
  return i === -1 ? undefined : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const fixtures = argValue(args, "--fixtures");
  if (!fixtures) usage();
  const alpha = Number(argValue(args, "--alpha") ?? "0.1");
  const out = argValue(args, "--out") ?? "reports/dispatch-latest.json";

  const data = JSON.parse(await readFile(path.resolve(fixtures!), "utf8")) as {
    calibration: AssetFeatures[];
    holdout: AssetFeatures[];
  };

  const { results, summary } = backtest(data.calibration, data.holdout, alpha);
  await mkdir(path.dirname(path.resolve(out)), { recursive: true });
  await writeFile(
    path.resolve(out),
    JSON.stringify({ alpha, q_hat: calibrateQuantile(data.calibration, alpha), summary, results }, null, 2) + "\n",
  );

  console.log("id\tdecision\trisk\tinterval\tset");
  for (const r of results) {
    console.log(
      `${r.id}\t${r.decision}\t${r.risk_score}\t[${r.conformal_interval.join(",")}]\t${r.prediction_set.join("|")}`,
    );
  }
  console.log(
    `coverage=${summary.empirical_coverage.toFixed(3)} target=${summary.target_coverage} n=${summary.n}`,
  );
  console.log(`Report: ${path.resolve(out)}`);
}

main().catch((e) => {
  console.error(e instanceof Error ? e.message : e);
  process.exit(1);
});
