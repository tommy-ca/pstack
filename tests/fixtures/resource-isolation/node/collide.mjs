#!/usr/bin/env node
// Colliding verification fixture: fixed port, shared state path, no barrier.
//
// Node twin of ../python/collide.py, using `node:` stdlib only. Two concurrent
// invocations take both resources from the environment (`CI_FIXTURE_PORT`,
// `CI_FIXTURE_STATE`) and start work immediately, so the second process loses
// the port bind and exits non-zero while the first is still holding the
// resource and polluting the shared state directory.
//
// Driven by tests/test_ci_resource_isolation.py as the negative control for
// isolated.mjs.

import fs from "node:fs";
import net from "node:net";
import path from "node:path";

const HOLD_DEFAULT = 2.0;
const HOLD_MIN = 0.05;
const HOLD_MAX = 10.0;

function holdMs() {
  const raw = Number.parseFloat(process.env.CI_FIXTURE_HOLD ?? "");
  const seconds = Number.isFinite(raw) ? raw : HOLD_DEFAULT;
  return Math.min(Math.max(seconds, HOLD_MIN), HOLD_MAX) * 1000;
}

const worker = process.argv[2] ?? "a";
const port = Number(process.env.CI_FIXTURE_PORT);
const state = path.resolve(process.env.CI_FIXTURE_STATE);

// Shared predictable path: every worker writes the same directory and the same
// `owner` file, so concurrent runs clobber each other's state.
fs.mkdirSync(state, { recursive: true });
fs.writeFileSync(path.join(state, "owner"), worker);
fs.writeFileSync(
  path.join(state, `${worker}.ready`),
  `${JSON.stringify({ worker, port, pid: process.pid })}\n`,
);

// Bounded dwell: the claim is held long enough for a concurrent peer to
// collide, and the process cannot hang if that peer never arrives.
const watchdog = setTimeout(() => process.exit(1), holdMs() + 5000);

const server = net.createServer();
server.once("error", (err) => {
  process.stderr.write(
    `COLLISION worker=${worker} port=${port} code=${err.code} ${err.message}\n`,
  );
  process.exit(1);
});
server.listen(port, "127.0.0.1", () => {
  process.stdout.write(
    `${JSON.stringify({ fixture: "collide", worker, port, pid: process.pid })}\n`,
  );
  setTimeout(() => {
    clearTimeout(watchdog);
    server.close(() => process.exit(0));
  }, holdMs());
});
