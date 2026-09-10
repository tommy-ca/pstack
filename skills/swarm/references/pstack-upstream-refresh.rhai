let meta = #{
    name: "pstack-upstream-refresh",
    description: "Refresh this Grok pstack port from official Cursor pstack without a second router.",
    when_to_use: "upstream Cursor pstack refresh, sync-from-upstream, overlay port, host-adapter migration across many skills.",
    phases: [
        #{ title: "Seed", detail: "Overlay last classification onto the new name-status" },
        #{ title: "Classify", detail: "Fill unclassified fragments. Pause if any remain." },
        #{ title: "Apply", detail: "Thin copy of permitted port and new-skill-lever rows" },
        #{ title: "Adapt", detail: "Run adapt-harness.py" },
        #{ title: "Check", detail: "apply-check leftover tokens, fences, remaps" },
        #{ title: "Interrogate", detail: "pack.py then pstack:interrogate-reviewers" },
        #{ title: "Verify", detail: "pstack:independent-verifier" },
    ],
};

let seed_schema = #{
    "type": "object",
    "required": ["ok", "overlay", "unclassified"],
    "properties": #{
        "ok": #{ "type": "boolean" },
        "overlay": #{ "type": "string" },
        "unclassified": #{ "type": "integer" },
        "summary": #{ "type": "string" },
    },
};
let classify_schema = #{
    "type": "object",
    "required": ["ok", "unclassified"],
    "properties": #{
        "ok": #{ "type": "boolean" },
        "unclassified": #{ "type": "integer" },
        "summary": #{ "type": "string" },
    },
};
let step_schema = #{
    "type": "object",
    "required": ["ok", "summary"],
    "properties": #{
        "ok": #{ "type": "boolean" },
        "summary": #{ "type": "string" },
    },
};

let cache = ".worktrees/upstream-cursor-plugins";
if args != () && args.cache != () && args.cache != "" {
    cache = args.cache;
}
let overlay = "/tmp/pstack-refresh/overlay.tsv";
let slices = "/tmp/pstack-refresh/slices";
let pack_dir = "/tmp/pstack-refresh/interrogate";

phase("Seed");
let seed_prompt = "";
seed_prompt += "You are the parent refresh worker. Use command/run_terminal_command. Do not copy blobs. ";
seed_prompt += "Cache path (JSON): " + json_encode(cache) + ". Overlay path: " + overlay + ". ";
seed_prompt += "1. python3 scripts/sync-from-upstream.py --log. ";
seed_prompt += "2. mkdir -p /tmp/pstack-refresh. ";
seed_prompt += "3. python3 skills/swarm/scripts/partition.py seed --cache " + cache + " --out " + overlay + ". ";
seed_prompt += "4. python3 skills/swarm/scripts/partition.py print --stats --table " + overlay + ". ";
seed_prompt += "Return ok=true only if seed wrote the overlay. unclassified is the unclassified count from --stats. overlay is the overlay path.";
let seed = agent(seed_prompt, #{
    label: "refresh-seed",
    agent_type: "pstack:swarm-workers",
    output_schema: seed_schema,
});
if seed == () || !seed.success || seed.output.ok != true {
    complete(#{ summary: "seed failed closed", ok: false });
}

phase("Classify");
let leftover = seed.output.unclassified;
if leftover == () {
    leftover = 1;
}
if leftover > 0 {
    let classify_prompt = "";
    classify_prompt += "Classify unclassified fragments only. Use command/run_terminal_command. ";
    classify_prompt += "Do not rewrite skills/swarm/references/classification.tsv. Do not copy blobs. ";
    classify_prompt += "Skip, host-owned, and audit are fences, not worker slices. ";
    classify_prompt += "Overlay: " + overlay + ". Slice dir: " + slices + ". Cache: " + json_encode(cache) + ". ";
    classify_prompt += "mkdir -p " + slices + "/worker-0 " + slices + "/worker-1 " + slices + "/worker-2 " + slices + "/worker-3 before any spawn cwd. ";
    classify_prompt += "Run: python3 skills/swarm/scripts/partition.py partition --table " + overlay + " --bucket unclassified --workers 4 --out " + slices + ". ";
    classify_prompt += "Read each worker-N.paths. Fill only those paths in a fragment TSV. Merge fragments back to " + overlay + ". ";
    classify_prompt += "Then python3 skills/swarm/scripts/partition.py print --coverage --cache " + cache + " --table " + overlay + ". ";
    classify_prompt += "Return ok=true only if coverage ok printed. unclassified is remaining unclassified count (0 if coverage passed).";
    let classify = agent(classify_prompt, #{
        label: "refresh-classify",
        agent_type: "pstack:swarm-workers",
        output_schema: classify_schema,
    });
    if classify == () || !classify.success || classify.output.ok != true {
        leftover = 1;
    } else {
        leftover = classify.output.unclassified;
        if leftover == () {
            leftover = 1;
        }
    }
}
if leftover > 0 {
    await_user("verification", "Unclassified rows remain in the overlay TSV. Classify them, then resume.");
}

phase("Apply");
let apply_prompt = "";
apply_prompt += "Thin copy only. Use command/run_terminal_command. port is intent, not a write permit. ";
apply_prompt += "Cache: " + json_encode(cache) + ". Table: " + overlay + ". Dest is this plugin cwd. ";
apply_prompt += "Run: python3 skills/swarm/scripts/apply.py --cache " + cache + " --table " + overlay + " --dest . --dry-run. ";
apply_prompt += "Then: python3 skills/swarm/scripts/apply.py --cache " + cache + " --table " + overlay + " --dest . ";
apply_prompt += "Refuse fences, unclassified, deletes, and remapped dests. Do not recopy a dest that already has host markers. ";
apply_prompt += "Return ok=true only if apply ran and printed a plan.";
let apply_r = agent(apply_prompt, #{
    label: "refresh-apply",
    agent_type: "pstack:swarm-workers",
    output_schema: step_schema,
});
if apply_r == () || !apply_r.success || apply_r.output.ok != true {
    complete(#{ summary: "apply failed closed", ok: false });
}

phase("Adapt");
let adapt_prompt = "";
adapt_prompt += "Use command/run_terminal_command in this plugin cwd. ";
adapt_prompt += "Run python3 scripts/adapt-harness.py. ";
adapt_prompt += "Return ok=true only if adapt-harness.py exited 0.";
let adapt_r = agent(adapt_prompt, #{
    label: "refresh-adapt",
    agent_type: "pstack:swarm-workers",
    output_schema: step_schema,
});
if adapt_r == () || !adapt_r.success || adapt_r.output.ok != true {
    complete(#{ summary: "adapt failed closed", ok: false });
}

phase("Check");
let check_prompt = "";
check_prompt += "Use command/run_terminal_command. Do not run git diff --name-status. ";
check_prompt += "Run python3 skills/swarm/scripts/partition.py apply-check --cache " + cache + " --table " + overlay + " --dest . ";
check_prompt += "apply-check must print apply-check ok. Coverage is partition.py print --coverage, a different command. ";
check_prompt += "Return ok=true only if apply-check ok printed.";
let check_r = agent(check_prompt, #{
    label: "refresh-apply-check",
    agent_type: "pstack:swarm-workers",
    output_schema: step_schema,
});
if check_r == () || !check_r.success || check_r.output.ok != true {
    complete(#{ summary: "apply-check failed closed", ok: false });
}

phase("Interrogate");
let pack_prompt = "";
pack_prompt += "Use command/run_terminal_command. mkdir -p " + pack_dir + ". ";
pack_prompt += "Write a one-paragraph intent file at " + pack_dir + "/intent.md describing this upstream refresh. ";
pack_prompt += "Pack reviewers with skills/interrogate/scripts/pack.py --intent " + pack_dir + "/intent.md plus exactly one of --range or --diff-file. ";
pack_prompt += "Point reviewers at the packed prompt.md. Do not inline the TSV. Return ok=true only if prompt.md exists.";
let pack_r = agent(pack_prompt, #{
    label: "refresh-pack",
    agent_type: "pstack:swarm-workers",
    output_schema: step_schema,
});
if pack_r == () || !pack_r.success || pack_r.output.ok != true {
    complete(#{ summary: "pack failed closed", ok: false });
}

let review_prompt = "";
review_prompt += "Adversarially review this upstream refresh. Use read_file and grep. ";
review_prompt += "Read " + pack_dir + "/prompt.md first. Do not answer from memory. ";
review_prompt += "Return ok=true only after you have read the packed prompt and the dest files it names.";
let review_jobs = [];
review_jobs.push(#{
    prompt: review_prompt,
    label: "refresh-review-a",
    agent_type: "pstack:interrogate-reviewers",
    isolation_worktree: true,
    output_schema: step_schema,
});
review_jobs.push(#{
    prompt: review_prompt,
    label: "refresh-review-b",
    agent_type: "pstack:interrogate-reviewers",
    isolation_worktree: true,
    output_schema: step_schema,
});
let reviews = parallel(review_jobs);
let review_ok = false;
for r in reviews {
    if r != () && r.success && r.output.ok == true {
        review_ok = true;
    }
}
if !review_ok {
    complete(#{ summary: "interrogate failed closed", ok: false });
}

phase("Verify");
let verify_prompt = "";
verify_prompt += "Independent verify. Use command/run_terminal_command and read_file. ";
verify_prompt += "Run python3 scripts/verify-harness.py. ";
verify_prompt += "Run python3 skills/swarm/scripts/partition.py print --coverage --cache " + cache + " --table " + overlay + ". ";
verify_prompt += "Run python3 skills/swarm/scripts/partition.py apply-check --cache " + cache + " --table " + overlay + " --dest . ";
verify_prompt += "Return ok=true only if those commands passed. Inconclusive is not a pass.";
let verify = agent(verify_prompt, #{
    label: "refresh-verify",
    agent_type: "pstack:independent-verifier",
    output_schema: step_schema,
});
if verify == () || !verify.success || verify.output.ok != true {
    complete(#{ summary: "independent verify failed closed", ok: false });
}
complete(#{ summary: "pstack-upstream-refresh ok", ok: true, overlay: overlay });
