import { describe, expect, it } from "bun:test";
import { existsSync, readFileSync } from "node:fs";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SCRIPT = join(import.meta.dir, "worktree-drop.sh");

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
});
