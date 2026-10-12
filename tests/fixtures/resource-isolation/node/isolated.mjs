#!/usr/bin/env node
// Isolated verification fixture: per-process port and private state root.
//
// Node twin of ../python/isolated.py, using `node:` stdlib only. Each worker
// listens on port 0 and keeps the server (atomic allocation, no scan-then-bind),
// works under its own mkdtemp root, publishes a ready marker, waits for the
// peer's marker before touching the peer, and then closes the listener and
// removes its root.
//
// `CI_FIXTURE_STATE` / `CI_FIXTURE_PORT` are never read here; the shared
// rendezvous directory the peers meet in comes from `CI_FIXTURE_RENDEZVOUS`.
// Contrast with collide.mjs; driven by tests/test_ci_resource_isolation.py.

import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";

const WAIT_DEFAULT = 15.0;
const WAIT_MIN = 0.05;
const WAIT_MAX = 60.0;

function waitMs() {
  const raw = Number.parseFloat(process.env.CI_FIXTURE_WAIT ?? "");
  const seconds = Number.isFinite(raw) ? raw : WAIT_DEFAULT;
  return Math.min(Math.max(seconds, WAIT_MIN), WAIT_MAX) * 1000;
}

function marker(name) {
  return path.join(rendezvous, name);
}

function writeMarker(name, payload) {
  fs.writeFileSync(marker(name), `${JSON.stringify(payload)}\n`);
}

function waitJson(file, deadline) {
  return new Promise((resolve, reject) => {
    const poll = () => {
      try {
        resolve(JSON.parse(fs.readFileSync(file, "utf8")));
        return;
      } catch {
        // not published yet
      }
      if (Date.now() >= deadline) {
        reject(Object.assign(new Error(`peer marker ${path.basename(file)} never appeared within the bounded wait`), { code: "PEER_TIMEOUT" }));
        return;
      }
      setTimeout(poll, 10);
    };
    poll();
  });
}

function connect(port) {
  return new Promise((resolve, reject) => {
    const socket = net.connect({ host: "127.0.0.1", port });
    socket.once("connect", () => socket.end(resolve));
    socket.once("error", reject);
  });
}

const worker = process.argv[2] ?? "a";
const peer = worker === "a" ? "b" : "a";
const rendezvous = path.resolve(process.env.CI_FIXTURE_RENDEZVOUS);
fs.mkdirSync(rendezvous, { recursive: true });

const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), `ci-fixture-${worker}-`));
fs.mkdirSync(path.join(tempRoot, "state"));
fs.writeFileSync(path.join(tempRoot, "state", "worker.json"), `${JSON.stringify({ worker })}\n`);

const server = net.createServer();
const sockets = new Set();
server.on("connection", (socket) => {
  sockets.add(socket);
  socket.once("close", () => sockets.delete(socket));
});
await new Promise((resolve, reject) => {
  server.once("error", reject);
  server.listen(0, "127.0.0.1", resolve);
});
const port = server.address().port;

const deadline = Date.now() + waitMs();
const events = ["allocated"];
let peerPort = 0;
let code = 0;
let failure = "";
try {
  writeMarker(`${worker}.ready`, { worker, port, temp_root: tempRoot, pid: process.pid });
  events.push("published");
  const ready = await waitJson(marker(`${peer}.ready`), deadline);
  peerPort = ready.port;
  events.push("observed-ready");
  // Peer step: only after the peer's readiness has been observed.
  await connect(peerPort);
  events.push("connected-peer");
  writeMarker(`${worker}.observed`, { worker, port });
  await waitJson(marker(`${peer}.observed`), deadline);
  events.push("peer-observed-us");
} catch (err) {
  if (err?.code === "PEER_TIMEOUT") {
    code = 3;
    failure = `ISOLATION-TIMEOUT worker=${worker} ${err.message}`;
  } else {
    code = 2;
    failure = `ISOLATION-PEER worker=${worker} peer=${peer} code=${err?.code} ${err?.message}`;
  }
} finally {
  for (const socket of sockets) {
    socket.destroy();
  }
  await new Promise((resolve) => server.close(resolve));
  fs.rmSync(tempRoot, { recursive: true, force: true });
  writeMarker(`${worker}.done`, { worker, code });
}

if (code) {
  process.stderr.write(`${failure}\n`);
  process.exit(code);
}
process.stdout.write(
  `${JSON.stringify({ fixture: "isolated", worker, port, temp_root: tempRoot, peer_port: peerPort, events })}\n`,
);
