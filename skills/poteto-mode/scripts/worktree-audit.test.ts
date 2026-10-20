import { describe, expect, it } from "bun:test";
import { existsSync } from "node:fs";
import { chmod, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SCRIPT = join(import.meta.dir, "worktree-audit.sh");

function git(repo: string, args: readonly string[]): string {
  const result = Bun.spawnSync(["git", "-C", repo, ...args]);
  if (result.exitCode !== 0) {
    throw new Error(
      `git ${args.join(" ")} failed: ${result.stderr.toString()}`
    );
  }
  return result.stdout.toString().trim();
}

describe("worktree-audit", () => {
  it("keeps spaced paths, reports unknown base refs, and reads an explicit transcript root", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-audit-"));
    try {
      const repo = join(directory, "repo");
      await mkdir(repo);
      git(repo, ["init", "--initial-branch=main"]);
      git(repo, ["config", "user.name", "Audit Test"]);
      git(repo, ["config", "user.email", "audit@example.com"]);
      await writeFile(join(repo, "main.txt"), "main\n");
      git(repo, ["add", "."]);
      git(repo, ["commit", "-m", "main"]);

      const worktree = join(directory, "candidate with spaces");
      git(repo, ["worktree", "add", "-b", "feature", worktree]);
      const transcripts = join(directory, "transcripts");
      await mkdir(transcripts);
      await writeFile(
        join(transcripts, "chat.json"),
        `${worktree}/main.txt\n`
      );

      const result = Bun.spawnSync(["bash", SCRIPT, repo], {
        env: { ...process.env, PSTACK_TRANSCRIPTS_DIR: transcripts },
      });
      expect(result.exitCode).toBe(0);
      const row = result.stdout
        .toString()
        .trim()
        .split("\n")
        .find((line) => line.endsWith(`\t${worktree}`));
      expect(row).toBeDefined();
      const fields = row?.split("\t") ?? [];
      expect(fields[2]).toBe("unknown");
      expect(fields[6]).not.toBe("-");
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });
  it("honours -b as the merge base and rejects flags it does not know", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-audit-base-"));
    try {
      const repo = join(directory, "repo");
      await mkdir(repo);
      git(repo, ["init", "--initial-branch=main"]);
      git(repo, ["config", "user.name", "Audit Test"]);
      git(repo, ["config", "user.email", "audit@example.com"]);
      await writeFile(join(repo, "main.txt"), "main\n");
      git(repo, ["add", "."]);
      git(repo, ["commit", "-m", "main"]);

      const worktree = join(directory, "feature");
      git(repo, ["worktree", "add", "-b", "feature", worktree]);
      await writeFile(join(worktree, "feature.txt"), "feature\n");
      git(worktree, ["add", "."]);
      git(worktree, ["commit", "-m", "feature"]);

      const transcripts = join(directory, "transcripts");
      await mkdir(transcripts);
      const env = { ...process.env, PSTACK_TRANSCRIPTS_DIR: transcripts };
      const row = (stdout: string): string[] =>
        stdout
          .trim()
          .split("\n")
          .find((candidate) => candidate.endsWith(`\t${worktree}`))
          ?.split("\t") ?? [];

      const based = Bun.spawnSync(["bash", SCRIPT, "-b", "main", repo], { env });
      expect(based.exitCode).toBe(0);
      expect(based.stdout.toString()).toContain("# base: main\n");
      expect(row(based.stdout.toString())[2]).toBe("no");

      const missing = Bun.spawnSync(["bash", SCRIPT, "-b", "nope", repo], { env });
      expect(missing.exitCode).toBe(0);
      expect(row(missing.stdout.toString())[2]).toBe("unknown");

      const needsRef = Bun.spawnSync(["bash", SCRIPT, "--base"], { env });
      expect(needsRef.exitCode).toBe(2);

      const help = Bun.spawnSync(["bash", SCRIPT, "-h"], { env });
      expect(help.exitCode).toBe(0);
      expect(help.stdout.toString()).toContain("Usage: worktree-audit.sh");
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("does not treat a closed PR as safe when the base is unknown", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-audit-"));
    try {
      const repo = join(directory, "repo");
      await mkdir(repo);
      git(repo, ["init", "--initial-branch=main"]);
      git(repo, ["config", "user.name", "Audit Test"]);
      git(repo, ["config", "user.email", "audit@example.com"]);
      await writeFile(join(repo, "main.txt"), "main\n");
      git(repo, ["add", "."]);
      git(repo, ["commit", "-m", "main"]);

      const worktree = join(directory, "candidate");
      git(repo, ["worktree", "add", "-b", "feature", worktree]);
      const bin = join(directory, "bin");
      await mkdir(bin);
      const gh = join(bin, "gh");
      await writeFile(
        gh,
        '#!/bin/sh\nprintf \'[{"number":123,"state":"CLOSED","headRefName":"feature"}]\\n\'\n'
      );
      await chmod(gh, 0o755);
      const transcripts = join(directory, "transcripts");
      await mkdir(transcripts);

      const result = Bun.spawnSync(["bash", SCRIPT, repo], {
        env: {
          ...process.env,
          PATH: `${bin}:${process.env.PATH ?? ""}`,
          PSTACK_TRANSCRIPTS_DIR: transcripts,
        },
      });
      expect(result.exitCode).toBe(0);
      const row = result.stdout
        .toString()
        .trim()
        .split("\n")
        .find((line) => line.endsWith(`\t${worktree}`));
      expect(row).toBeDefined();
      const fields = row?.split("\t") ?? [];
      expect(fields[2]).toBe("unknown");
      expect(fields[5].toLowerCase()).toBe("#123/closed");
      expect(fields[7]).toBe("hold-closed-unmerged");
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("lists leftover clones under PSTACK_LEFTOVER_PARENT and skips gitfile worktrees", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-audit-clone-"));
    try {
      const repo = join(directory, "repo");
      await mkdir(repo);
      git(repo, ["init", "--initial-branch=main"]);
      git(repo, ["config", "user.name", "Audit Test"]);
      git(repo, ["config", "user.email", "audit@example.com"]);
      await writeFile(join(repo, "main.txt"), "main\n");
      git(repo, ["add", "."]);
      git(repo, ["commit", "-m", "main"]);

      const worktree = join(directory, "linked");
      git(repo, ["worktree", "add", "-b", "feature", worktree]);

      const leftoverParent = join(directory, "leftovers");
      const clone = join(leftoverParent, "clone");
      await mkdir(clone, { recursive: true });
      git(clone, ["init", "--initial-branch=main"]);
      git(clone, ["config", "user.name", "Audit Test"]);
      git(clone, ["config", "user.email", "audit@example.com"]);
      await writeFile(join(clone, "clone.txt"), "clone\n");
      git(clone, ["add", "."]);
      git(clone, ["commit", "-m", "clone"]);

      const wrongSource = join(leftoverParent, "wrong-source");
      await mkdir(wrongSource, { recursive: true });
      git(wrongSource, ["init", "--initial-branch=main"]);
      git(wrongSource, ["config", "user.name", "Audit Test"]);
      git(wrongSource, ["config", "user.email", "audit@example.com"]);
      await writeFile(join(wrongSource, "wrong.txt"), "wrong\n");
      git(wrongSource, ["add", "."]);
      git(wrongSource, ["commit", "-m", "wrong"]);
      await writeFile(
        join(wrongSource, ".git", "grok-worktree-source"),
        "/other/repo\n"
      );

      const gitfileDir = join(leftoverParent, "gitfile");
      await mkdir(gitfileDir);
      await writeFile(join(gitfileDir, ".git"), "gitdir: /tmp/not-a-worktree\n");

      const transcripts = join(directory, "transcripts");
      await mkdir(transcripts);

      const result = Bun.spawnSync(["bash", SCRIPT, repo], {
        env: {
          ...process.env,
          PSTACK_TRANSCRIPTS_DIR: transcripts,
          PSTACK_LEFTOVER_PARENT: leftoverParent,
        },
      });
      expect(result.exitCode).toBe(0);
      const lines = result.stdout.toString().trim().split("\n");
      const cloneRow = lines.find((line) => line.endsWith(`\t${clone}`));
      expect(cloneRow).toBeDefined();
      const cloneFields = cloneRow?.split("\t") ?? [];
      expect(cloneFields[4]).toBe("clone");
      expect(cloneFields[7]).toBe("review");
      expect(cloneFields[cloneFields.length - 1]).toBe(clone);

      const linkedRow = lines.find((line) => line.endsWith(`\t${worktree}`));
      expect(linkedRow).toBeDefined();
      const linkedFields = linkedRow?.split("\t") ?? [];
      expect(linkedFields[4]).not.toBe("clone");
      expect(linkedFields[linkedFields.length - 1]).toBe(worktree);

      expect(lines.some((line) => line.endsWith(`\t${gitfileDir}`))).toBe(false);
      expect(lines.some((line) => line.endsWith(`\t${wrongSource}`))).toBe(
        false
      );
      expect(existsSync(clone)).toBe(true);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

  it("detects untracked files and classifies as scratch even when status.showUntrackedFiles=no is configured", async () => {
    const directory = await mkdtemp(join(tmpdir(), "worktree-audit-hidden-"));
    try {
      const repo = join(directory, "repo");
      await mkdir(repo);
      git(repo, ["init", "--initial-branch=main"]);
      git(repo, ["config", "user.name", "Audit Test"]);
      git(repo, ["config", "user.email", "audit@example.com"]);
      await writeFile(join(repo, "main.txt"), "main\n");
      git(repo, ["add", "."]);
      git(repo, ["commit", "-m", "main"]);

      const worktree = join(directory, "hidden-scratch");
      git(repo, ["worktree", "add", "-b", "hidden-scratch", worktree]);
      git(worktree, ["config", "status.showUntrackedFiles", "no"]);
      await writeFile(join(worktree, "untracked.txt"), "should not be hidden\n");

      const result = Bun.spawnSync(["bash", SCRIPT, repo]);
      expect(result.exitCode).toBe(0);
      const lines = result.stdout.toString().trim().split("\n");
      const row = lines.find((line) => line.endsWith(`\t${worktree}`));
      expect(row).toBeDefined();
      const fields = row?.split("\t") ?? [];
      expect(fields[3]).toBe("scratch:1");
      expect(fields[7]).toBe("hold-untracked");
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });

});
