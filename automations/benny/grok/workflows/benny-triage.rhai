let meta = #{
    name: "benny-triage",
    description: "Triage one Slack report. One thread-only verdict with a Benny marker.",
    phases: [
        #{ title: "Preflight", detail: "require args.thread_url" },
        #{ title: "Triage", detail: "read the operational SKILL.md and post one marker" },
    ],
};

let verdict_schema = #{
    "type": "object", "required": ["marker", "posted_in_thread"],
    "properties": #{
        "marker": #{ "type": "string" },
        "posted_in_thread": #{ "type": "boolean" },
        "tracker": #{ "type": "string" },
        "reason": #{ "type": "string" },
    },
};

let permalink = if args == () { () } else { args.thread_url };
if permalink == () { pause("verification", "Pass args.thread_url, the Slack thread permalink."); }

phase("Preflight");
log("thread_url=" + permalink);

phase("Triage");
let prompt = "";
prompt += "Read automations/benny/skills/triage-issue-reports/SKILL.md with read_file and follow it. ";
prompt += "Source thread: " + json_encode(permalink) + ". ";
prompt += "Freeze source channel and root thread_ts before any write. ";
prompt += "Never post a source-channel root message. ";
prompt += "Delegated workers get no Slack write tools. ";
prompt += "Post exactly one thread reply ending with [benny:bug], [benny:performance], or [benny:other]. ";
prompt += "Use grep and read_file on the repo. Fail closed if config is missing. ";
prompt += "Return {marker, posted_in_thread, tracker, reason}.";

let r = agent(prompt, #{
    label: "benny-triage",
    capability_mode: "execute",
    output_schema: verdict_schema,
});
if r == () || !r.success || r.output.marker == () {
    complete(#{ summary: "triage failed closed", posted_in_thread: false });
}
complete(r.output);
