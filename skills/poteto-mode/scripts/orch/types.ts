export type Verdict =
  | "live-ui-verified"
  | "unit-test-verified"
  | "type-check-only"
  | "verifier-blocked"
  | "verifier-failed";

export interface Unit {
  readonly id: string;
  readonly track: string;
  readonly state: string;
  readonly branch: string;
  readonly pr: string;
  readonly sha: string;
  readonly brief: string;
}

export interface LedgerEntry {
  readonly pr: string;
  readonly sha: string;
  readonly verdict: Verdict;
  readonly evidence: string;
  readonly verifier: string;
  readonly ts: string;
}

export interface InboxPointer {
  readonly ts: string;
  readonly agent: string;
  readonly unit: string;
  readonly status: string;
  readonly report: string;
}

export interface InboxPushResult {
  readonly pointer: InboxPointer;
  readonly filename: string;
}

export interface OpenGate {
  readonly kind: "open";
  readonly id: string;
  readonly question: string;
  readonly options: string;
  readonly defaultAnswer: string;
}

export interface ResolvedGate {
  readonly kind: "resolved";
  readonly id: string;
  readonly question: string;
  readonly options: string;
  readonly defaultAnswer: string;
  readonly answer: string;
}

export type Gate = OpenGate | ResolvedGate;

export type FrontierPrState = "OPEN" | "MERGED" | "CLOSED";

export interface FrontierPr {
  readonly pr: number;
  readonly branches: string;
  readonly sha: string;
  readonly state: FrontierPrState;
}

export interface Frontier {
  readonly generation: number;
  readonly prs: readonly FrontierPr[];
  readonly lowestUnmerged: number | null;
}

export interface StandingLine {
  readonly number: number;
  readonly line: string;
}

export type Counts = Readonly<Record<string, number>>;

export interface StatusSummary {
  readonly unitStates: Counts;
  readonly ledgerVerdicts: Counts;
  readonly frontierGeneration: number;
  readonly openGateIds: readonly string[];
}

export interface StatusReport {
  readonly units: readonly Unit[];
  readonly ledger: readonly LedgerEntry[];
  readonly frontier: Frontier;
  readonly gates: readonly Gate[];
  readonly summary: StatusSummary;
  readonly changed: string;
}

export interface AddUnitParams {
  readonly id: string;
  readonly track: string;
  readonly brief?: string;
}

export interface SetUnitParams {
  readonly id: string;
  readonly state: string;
  readonly branch?: string;
  readonly pr?: number;
  readonly sha?: string;
}

export interface ListUnitsParams {
  readonly state?: string;
  readonly track?: string;
}

export interface RecordLedgerParams {
  readonly pr: number;
  readonly sha: string;
  readonly verdict: Verdict;
  readonly evidence: string;
  readonly verifier?: string;
}

export interface CheckLedgerParams {
  readonly pr: number;
  readonly sha: string;
}

export interface PushInboxParams {
  readonly agent: string;
  readonly unit: string;
  readonly status: string;
  readonly report?: string;
}

export interface ParkGateParams {
  readonly id: string;
  readonly question: string;
  readonly options: string;
  readonly defaultAnswer: string;
}

export interface ResolveGateParams {
  readonly id: string;
  readonly answer: string;
}

export type Forge = "gh" | "origin";

export interface SetFrontierParams {
  readonly repo: string;
  readonly forge?: Forge;
  readonly prs?: readonly number[];
}

export interface AddStandingParams {
  readonly line: string;
}

export interface OpenStoreOptions {
  readonly force?: boolean;
  readonly onLockStolen?: (holder: string) => void;
  readonly onStaleLock?: (holder: string) => void;
}

export interface Store {
  readonly units: {
    readonly add: (params: AddUnitParams) => Promise<Unit>;
    readonly set: (params: SetUnitParams) => Promise<Unit>;
    readonly get: (id: string) => Promise<Unit>;
    readonly list: (params?: ListUnitsParams) => Promise<readonly Unit[]>;
    readonly counts: () => Promise<Counts>;
  };
  readonly ledger: {
    readonly record: (params: RecordLedgerParams) => Promise<LedgerEntry>;
    readonly check: (params: CheckLedgerParams) => Promise<LedgerEntry>;
    readonly summary: () => Promise<Counts>;
  };
  readonly inbox: {
    readonly push: (params: PushInboxParams) => Promise<InboxPushResult>;
    readonly drain: () => Promise<readonly InboxPointer[]>;
    readonly peek: () => Promise<readonly InboxPointer[]>;
    readonly count: () => Promise<number>;
  };
  readonly gates: {
    readonly park: (params: ParkGateParams) => Promise<OpenGate>;
    readonly list: () => Promise<readonly OpenGate[]>;
    readonly resolve: (params: ResolveGateParams) => Promise<ResolvedGate>;
  };
  readonly frontier: {
    readonly set: (params: SetFrontierParams) => Promise<Frontier>;
    readonly show: () => Promise<Frontier>;
  };
  readonly standing: {
    readonly show: () => Promise<readonly StandingLine[]>;
    readonly add: (params: AddStandingParams) => Promise<StandingLine>;
  };
  readonly status: {
    readonly render: () => Promise<StatusReport>;
  };
  readonly init: () => Promise<{ readonly store: string }>;
  readonly close: () => Promise<void>;
}

export interface NotFoundOutput {
  readonly compact: string;
  readonly json: unknown;
}

export class UserError extends Error {}
export class UsageError extends UserError {}
export class NotFoundError extends UserError {
  public constructor(
    message: string,
    public readonly output?: NotFoundOutput
  ) {
    super(message);
  }
}

export function errorCode(error: unknown): string | null {
  if (
    error !== null &&
    typeof error === "object" &&
    "code" in error &&
    typeof error.code === "string"
  ) {
    return error.code;
  }
  return null;
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function isUnknownArray(value: unknown): value is readonly unknown[] {
  return Array.isArray(value);
}

export function verdictOrNull(value: string): Verdict | null {
  switch (value) {
    case "live-ui-verified":
    case "unit-test-verified":
    case "type-check-only":
    case "verifier-blocked":
    case "verifier-failed":
      return value;
    default:
      return null;
  }
}

export function frontierPrStateOrNull(value: unknown): FrontierPrState | null {
  switch (value) {
    case "OPEN":
    case "MERGED":
    case "CLOSED":
      return value;
    default:
      return null;
  }
}

export function parseVerdict(value: string): Verdict {
  const verdict = verdictOrNull(value);
  if (verdict === null) {
    throw new UserError(
      "verdict must be live-ui-verified, unit-test-verified, type-check-only, verifier-blocked, or verifier-failed"
    );
  }
  return verdict;
}

export function cleanCell(value: string): string {
  const cleaned = value.replace(/[\t\n\r]/g, " ");
  return /^[=+\-@]/.test(cleaned) ? `'${cleaned}` : cleaned;
}

export function requiredCell(value: string, label: string): string {
  const cleaned = cleanCell(value);
  if (cleaned.trim().length === 0) {
    throw new UserError(`${label} must not be empty`);
  }
  return cleaned;
}

export function requiredLine(value: string, label: string): string {
  const cleaned = value.replace(/[\n\r]/g, " ").trim();
  if (cleaned.length === 0) {
    throw new UserError(`${label} must not be empty`);
  }
  return cleaned;
}

export function positiveInteger(value: number, label: string): number {
  if (!Number.isSafeInteger(value) || value < 1) {
    throw new UserError(`${label} must be a positive integer`);
  }
  return value;
}

export function parseForge(value: string): Forge {
  if (value === "gh" || value === "origin") {
    return value;
  }
  throw new UserError("forge must be gh or origin");
}
