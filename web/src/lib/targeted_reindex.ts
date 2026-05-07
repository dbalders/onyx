/**
 * Client for the targeted-reindex flow.
 *
 * One Resolve-All click on the admin Indexing-Errors modal can carry
 * thousands of unresolved error_ids; the server caps a single request
 * at `MAX_TARGETS_PER_REQUEST = 100`. This module:
 *
 *   - fetches all unresolved error_ids for a cc_pair (paginated loop);
 *   - chunks them into ≤100-id batches;
 *   - submits each batch sequentially (back-pressure on the PRIMARY
 *     celery queue — the trigger task lives there);
 *   - polls each returned job until terminal;
 *   - returns the aggregated counts so the UI can update in one shot.
 */
import {
  IndexAttemptError,
  PaginatedIndexAttemptErrors,
  TargetedReindexJobStatus,
  TargetedReindexResponse,
} from "@/app/admin/connector/[ccPairId]/types";

/** Server-enforced cap. Keep in sync with `MAX_TARGETS_PER_REQUEST`
 * in `backend/onyx/db/targeted_reindex.py`. */
export const TARGETED_REINDEX_MAX_PER_REQUEST = 100;

/** How often to poll the GET status endpoint while a batch runs. */
const POLL_INTERVAL_MS = 2000;

/** Aggregated outcome of a `resolveAll` run across N batches. */
export interface ResolveAllResult {
  job_ids: number[];
  resolved_count: number;
  still_failing_count: number;
  skipped_count: number;
  /** Errors whose target's doc successfully landed during reindex. */
  resolved_error_ids: number[];
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Page through `/api/manage/admin/cc-pair/{cc_pair_id}/errors` and
 * collect every unresolved error in a single flat list. The endpoint
 * caps page_size at 100. */
export async function fetchAllUnresolvedErrors(
  ccPairId: number
): Promise<IndexAttemptError[]> {
  const pageSize = 100;
  const collected: IndexAttemptError[] = [];
  let pageNum = 0;

  while (true) {
    const url =
      `/api/manage/admin/cc-pair/${ccPairId}/errors` +
      `?page_num=${pageNum}&page_size=${pageSize}&include_resolved=false`;
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed to fetch indexing errors (status ${res.status})`);
    }
    const page: PaginatedIndexAttemptErrors = await res.json();
    collected.push(...page.items);

    if (page.items.length < pageSize) break;
    pageNum += 1;

    // Defensive: hard cap the loop to avoid runaway pagination if the
    // server starts returning constant-size pages.
    if (collected.length >= page.total_items) break;
  }

  return collected;
}

/** Slice an array into fixed-size chunks. */
function chunk<T>(items: T[], size: number): T[][] {
  if (size <= 0) return [items];
  const out: T[][] = [];
  for (let i = 0; i < items.length; i += size) {
    out.push(items.slice(i, i + size));
  }
  return out;
}

/** Submit one batch of error_ids. */
async function submitBatch(
  errorIds: number[]
): Promise<TargetedReindexResponse> {
  const res = await fetch("/api/manage/admin/indexing/targeted-reindex", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ error_ids: errorIds }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(
      `targeted-reindex POST failed (status ${res.status}): ${body}`
    );
  }
  return res.json();
}

const TERMINAL_STATUSES: TargetedReindexJobStatus["status"][] = [
  "success",
  "failed",
  "completed_with_errors",
  "canceled",
];

/** Poll a job until it reaches a terminal status. */
async function pollJob(jobId: number): Promise<TargetedReindexJobStatus> {
  while (true) {
    const res = await fetch(
      `/api/manage/admin/indexing/targeted-reindex/${jobId}`
    );
    if (!res.ok) {
      throw new Error(
        `targeted-reindex GET failed (status ${res.status}) for job ${jobId}`
      );
    }
    const status: TargetedReindexJobStatus = await res.json();
    if (TERMINAL_STATUSES.includes(status.status)) {
      return status;
    }
    await sleep(POLL_INTERVAL_MS);
  }
}

/**
 * End-to-end Resolve-All for one cc_pair: fetch all unresolved errors,
 * chunk into N batches, submit each batch sequentially, poll each job
 * to terminal, return aggregated counts.
 *
 * Sequential (not parallel) by design — every batch routes through the
 * `PRIMARY` celery queue which is shared with the indexing scheduler.
 * Fanning out N parallel jobs would create scheduler backpressure.
 *
 * `onProgress` (optional) fires after each batch completes; useful for
 * inline progress UI ("3 / 7 batches done").
 */
export async function resolveAllErrorsForCCPair(
  ccPairId: number,
  onProgress?: (done: number, total: number) => void
): Promise<ResolveAllResult> {
  const errors = await fetchAllUnresolvedErrors(ccPairId);
  if (errors.length === 0) {
    return {
      job_ids: [],
      resolved_count: 0,
      still_failing_count: 0,
      skipped_count: 0,
      resolved_error_ids: [],
    };
  }

  const errorIds = errors.map((e) => e.id);
  const batches = chunk(errorIds, TARGETED_REINDEX_MAX_PER_REQUEST);

  const aggregate: ResolveAllResult = {
    job_ids: [],
    resolved_count: 0,
    still_failing_count: 0,
    skipped_count: 0,
    resolved_error_ids: [],
  };

  for (let i = 0; i < batches.length; i += 1) {
    const batch = batches[i];
    if (batch === undefined) continue;
    const submitted = await submitBatch(batch);
    aggregate.job_ids.push(submitted.targeted_reindex_job_id);

    const finalStatus = await pollJob(submitted.targeted_reindex_job_id);
    aggregate.resolved_count += finalStatus.resolved_count;
    aggregate.still_failing_count += finalStatus.still_failing_count;
    aggregate.skipped_count += finalStatus.skipped_count;
    aggregate.resolved_error_ids.push(
      ...finalStatus.resolved_summary.map((row) => row.id)
    );

    onProgress?.(i + 1, batches.length);
  }

  return aggregate;
}
