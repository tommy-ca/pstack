import { open, readFile, unlink } from "node:fs/promises";
import { join } from "node:path";
import {
  type OpenStoreOptions,
  UserError,
  errorCode,
} from "./types.ts";

export const LOCK_FILE = ".orch.lock";

export function holderIsDead(holder: string): boolean {
  const pid = Number.parseInt(holder, 10);
  if (!Number.isSafeInteger(pid) || pid <= 0 || String(pid) !== holder) {
    return false;
  }
  try {
    process.kill(pid, 0);
    return false;
  } catch (error) {
    return errorCode(error) === "ESRCH";
  }
}

export async function acquireLock(
  store: string,
  options: OpenStoreOptions
): Promise<() => Promise<void>> {
  const path = join(store, LOCK_FILE);
  const pid = String(process.pid);
  const create = async (): Promise<void> => {
    const handle = await open(path, "wx");
    await handle.writeFile(`${pid}\n`);
    await handle.close();
  };

  const takeOver = async (): Promise<void> => {
    await unlink(path);
    try {
      await create();
    } catch (retryError) {
      if (errorCode(retryError) === "EEXIST") {
        const retryHolder =
          (await readFile(path, "utf8")).trim() || "unknown";
        throw new UserError(`store lock held by pid ${retryHolder}`);
      }
      throw retryError;
    }
  };

  try {
    await create();
  } catch (error) {
    if (errorCode(error) !== "EEXIST") {
      throw error;
    }
    let holder = "unknown";
    try {
      holder = (await readFile(path, "utf8")).trim() || "unknown";
    } catch {
      holder = "unknown";
    }
    if (holderIsDead(holder)) {
      options.onStaleLock?.(holder);
      await takeOver();
    } else if (options.force) {
      options.onLockStolen?.(holder);
      await takeOver();
    } else {
      throw new UserError(`store lock held by pid ${holder}`);
    }
  }

  return async (): Promise<void> => {
    try {
      if ((await readFile(path, "utf8")).trim() === pid) {
        await unlink(path);
      }
    } catch (error) {
      if (errorCode(error) !== "ENOENT") {
        throw error;
      }
    }
  };
}
