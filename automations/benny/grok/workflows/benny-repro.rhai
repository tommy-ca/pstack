let meta = #{
    name: "benny-repro",
    description: "Wait for a trusted Benny marker, reproduce twice through real UI, draft PR only after proof.",
    phases: [
        #{ title: "Preflight", detail: "require args.thread_url" },
        #{ title: "Repro", detail: "read the operational SKILL.md and fail closed without a trusted marker" },
    ],
};

let result_schema = #{
    "type": "object", "required": ["outcome"],
    "properties": #{
        "outcome": #{ "type": "string" },
        "draft_pr": #{ "type": "string" },
        "reason": #{ "type": "string" },
    },
};

let permalink = if args == () { () } else { args.thread_url };
if permalink == () { pause("verification", "Pass args.thread_url, the Slack thread permalink."); }

phase("Preflight");
log("thread_url=" + permalink);

phase("Repro");
let prompt = "";
prompt += "Read automations/benny/skills/reproduce-and-fix-issues/SKILL.md with read_file and follow it. ";
prompt += "Source thread: " + json_encode(permalink) + ". ";
prompt += "Wait for a trusted [benny:bug] or [benny:performance] marker from the configured triage identity. ";
prompt += "Stop for [benny:other], a missing verdict, or an untrusted author. ";
prompt += "Never post a source-channel root message. Never merge or deploy. Draft pull requests only. ";
prompt += "Reproduce the discriminating symptom twice through the real UI. ";
prompt += "A unit test or injected state is not a repro. ";
prompt += "Return {outcome, draft_pr, reason}.";

let r = agent(prompt, #{
    label: "benny-repro",
    capability_mode: "execute",
    output_schema: result_schema,
});
if r == () || !r.success || r.output.outcome == () {
    complete(#{ summary: "repro failed closed", outcome: "blocked" });
}
complete(r.output);
