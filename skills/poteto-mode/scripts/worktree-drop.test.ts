import { describe, expect, it } from "bun:test";
import { existsSync, readFileSync } from "node:fs";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SCRIPT = join(import.meta.dir, "worktree-drop.sh");
const AUDIT = join(import.meta.dir, "worktree-audit.sh");

function git(repo: string, args: readonly string[]): string {
  const result = Bun.spawnSync(["git", "-C", repo, ...args]);
  if (result.exitCode !== 0) {
    throw new Error(
      `git ${args.join(" ")} failed: ${result.stderr.toString()}`
    );
  }
  return result.stdout.toString().trim();
}

function drop(
  args: readonly string[],
  extraEnv: Record<string, string> = {}
): { exitCode: number; stdout: string; stderr: string } {
  const result = Bun.spawnSync(["bash", SCRIPT, ...args], {
    env: { ...process.env, ...extraEnv },
  });
  return {
    exitCode: result.exitCode ?? 1,
    stdout: result.stdout.toString(),
    stderr: result.stderr.toString(),
  };
}

async function initRepo(path: string): Promise<void> {
  await mkdir(path, { recursive: true });
  git(path, ["init", "--initial-branch=main"]);
  git(path, ["config", "user.name", "Drop Test"]);
  git(path, ["config", "user.email", "drop@example.com"]);
  await writeFile(join(path, "main.txt"), "main\n");
  git(path, ["add", "."]);
  git(path, ["commit", "-m", "main"]);
}

describe("worktree-drop", () => {
  it("keeps host paths and branch deletes out of the script", () => {
    const source = readFileSync(SCRIPT, "utf8");
    expect(source.includes("/home/tommyk")).toBe(false);
    expect(source.includes("branch -D")).toBe(false);
  });

  it("dry-runs then applies registered extras and leftover clones, holding overlay and branch", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-drop-"));
    try {
      const repo = join(directory, "repo");
      await initRepo(repo);

      const extra = join(directory, "extra");
      git(repo, ["worktree", "add", "-b", "feature", extra]);

      const leftoverParent = join(directory, "leftovers");
      const clone = join(leftoverParent, "clone");
      await initRepo(clone);
      await writeFile(join(clone, ".git", "grok-worktree-source"), `${repo}\n`);

      const overlay = join(repo, ".worktrees", "upstream-cursor-plugins");
      await initRepo(overlay);

      const dry = drop([
        "--repo",
        repo,
        "--dry-run",
        "--expect-registered",
        "1",
        "--expect-leftover",
        "1",
        "--leftover-parent",
        leftoverParent,
      ]);
      expect(dry.exitCode).toBe(0);
      expect(existsSync(extra)).toBe(true);
      expect(existsSync(clone)).toBe(true);
      expect(existsSync(overlay)).toBe(true);

      const wrongRepo = drop([
        "--repo",
        clone,
        "--dry-run",
        "--expect-registered",
        "0",
        "--expect-leftover",
        "0",
        "--leftover-parent",
        leftoverParent,
      ]);
      expect(wrongRepo.exitCode).not.toBe(0);

      const overlayAsRepo = drop([
        "--repo",
        overlay,
        "--dry-run",
        "--expect-registered",
        "0",
        "--expect-leftover",
        "1",
        "--leftover-parent",
        leftoverParent,
      ]);
      expect(overlayAsRepo.exitCode).not.toBe(0);
      expect(existsSync(clone)).toBe(true);

      const applied = drop([
        "--repo",
        repo,
        "--apply",
        "--expect-registered",
        "1",
        "--expect-leftover",
        "1",
        "--leftover-parent",
        leftoverParent,
        "--path",
        extra,
        "--path",
        clone,
      ]);
      expect(applied.exitCode).toBe(0);
      expect(applied.stderr).toBe("");

      const porcelain = git(repo, ["worktree", "list", "--porcelain"]);
      const trees = porcelain
        .split("\n")
        .filter((line) => line.startsWith("worktree "))
        .map((line) => line.slice("worktree ".length));
      expect(trees).toEqual([repo]);
      expect(existsSync(clone)).toBe(false);
      expect(existsSync(overlay)).toBe(true);
      expect(git(repo, ["branch", "--list", "feature"])).toContain("feature");
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("refuses non-numeric --expect-registered on dry-run", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-drop-abc-"));
    try {
      const repo = join(directory, "repo");
      await initRepo(repo);
      const result = drop([
        "--repo",
        repo,
        "--dry-run",
        "--expect-registered",
        "abc",
        "--expect-leftover",
        "0",
      ]);
      expect(result.exitCode).not.toBe(0);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("refuses overlay clone as --repo", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-drop-overlay-"));
    try {
      const repo = join(directory, "repo");
      await initRepo(repo);
      const overlay = join(repo, ".worktrees", "upstream-cursor-plugins");
      await initRepo(overlay);
      const result = drop([
        "--repo",
        overlay,
        "--dry-run",
        "--expect-registered",
        "0",
        "--expect-leftover",
        "0",
      ]);
      expect(result.exitCode).not.toBe(0);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("refuses --apply without --path", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-drop-nopath-"));
    try {
      const repo = join(directory, "repo");
      await initRepo(repo);
      const extra = join(directory, "extra");
      git(repo, ["worktree", "add", "-b", "feature", extra]);
      const result = drop([
        "--repo",
        repo,
        "--apply",
        "--expect-registered",
        "1",
        "--expect-leftover",
        "0",
      ]);
      expect(result.exitCode).not.toBe(0);
      expect(existsSync(extra)).toBe(true);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("applies --path of one extra and leaves the other extra", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-drop-onepath-"));
    try {
      const repo = join(directory, "repo");
      await initRepo(repo);
      const keep = join(directory, "keep");
      const dropExtra = join(directory, "drop-extra");
      git(repo, ["worktree", "add", "-b", "keep-branch", keep]);
      git(repo, ["worktree", "add", "-b", "drop-branch", dropExtra]);
      const result = drop([
        "--repo",
        repo,
        "--apply",
        "--expect-registered",
        "2",
        "--expect-leftover",
        "0",
        "--path",
        dropExtra,
      ]);
      expect(result.exitCode).toBe(0);
      expect(existsSync(dropExtra)).toBe(false);
      expect(existsSync(keep)).toBe(true);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("counts an unmarked leftover clone in audit and drop leftover_count", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-drop-unmarked-"));
    try {
      const repo = join(directory, "repo");
      await initRepo(repo);
      const leftoverParent = join(directory, "leftovers");
      const clone = join(leftoverParent, "clone");
      await initRepo(clone);
      const transcripts = join(directory, "transcripts");
      await mkdir(transcripts);

      const audit = Bun.spawnSync(["bash", AUDIT, repo], {
        env: {
          ...process.env,
          PSTACK_TRANSCRIPTS_DIR: transcripts,
          PSTACK_LEFTOVER_PARENT: leftoverParent,
        },
      });
      expect(audit.exitCode).toBe(0);
      const auditLines = audit.stdout.toString().trim().split("\n");
      expect(auditLines.some((line) => line.endsWith(`\t${clone}`))).toBe(true);

      const listed = drop([
        "--repo",
        repo,
        "--dry-run",
        "--expect-registered",
        "0",
        "--expect-leftover",
        "1",
        "--leftover-parent",
        leftoverParent,
      ]);
      expect(listed.exitCode).toBe(0);
      expect(listed.stdout).toContain("leftover_count\t1");
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("does not count a leftover with the wrong grok-worktree-source", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-drop-wrongsrc-"));
    try {
      const repo = join(directory, "repo");
      await initRepo(repo);
      const leftoverParent = join(directory, "leftovers");
      const clone = join(leftoverParent, "clone");
      await initRepo(clone);
      await writeFile(
        join(clone, ".git", "grok-worktree-source"),
        "/other/repo\n"
      );
      const transcripts = join(directory, "transcripts");
      await mkdir(transcripts);

      const audit = Bun.spawnSync(["bash", AUDIT, repo], {
        env: {
          ...process.env,
          PSTACK_TRANSCRIPTS_DIR: transcripts,
          PSTACK_LEFTOVER_PARENT: leftoverParent,
        },
      });
      expect(audit.exitCode).toBe(0);
      const auditLines = audit.stdout.toString().trim().split("\n");
      expect(auditLines.some((line) => line.endsWith(`\t${clone}`))).toBe(
        false
      );

      const listed = drop([
        "--repo",
        repo,
        "--dry-run",
        "--expect-registered",
        "0",
        "--expect-leftover",
        "0",
        "--leftover-parent",
        leftoverParent,
      ]);
      expect(listed.exitCode).toBe(0);
      expect(listed.stdout).toContain("leftover_count\t0");
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });
});
