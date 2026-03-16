# Contributing

Thanks for considering a contribution.

SigmaCLI is a small operator-first repo, so the most valuable PRs are usually the ones that make the repo **truer, clearer, or more useful** — not just larger.

## What kind of repo this is

This is:

- an evidence-first Sigma CLI for BNB Chain / BSC
- strongest on capture, decode, planning, and read-only inspection
- intentionally cautious about execution claims

This is **not**:

- a production trading bot
- a generic wallet automation framework
- a place to overstate support because a route merely renders or a bundle hints at it

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

Basic sanity checks:

```bash
./sigma --help
./sigma account --help
python3 -m compileall sigma_operator
```

## Project layout

- `sigma` — launcher
- `sigma_operator/cli.py` — CLI wiring
- `sigma_operator/account.py` — read-only account and state inspection
- `sigma_operator/decode.py` — decode pipeline
- `sigma_operator/operations.py` — operation taxonomy / route hints
- `sigma_operator/surface_truth.py` — route-truth registry
- `README.md` — public repo entrypoint
- `STATUS.md` — compact current truth
- `SPEC.md` — public-facing project spec
- `COMMAND_MATURITY.md` — command/surface maturity policy
- `SIGMA_RUN_LEDGER.md` — historical verification record

## Contribution rules that matter here

### 1) Keep claims honest

If a PR changes what the repo claims publicly, update the docs accordingly.

Typical places to update:

- `README.md`
- `STATUS.md`
- `SPEC.md`
- `COMMAND_MATURITY.md`
- `SIGMA_RUN_LEDGER.md` when new verification evidence exists

### 2) Preserve evidence boundaries

Do not upgrade a route or command from planned/scaffold/alpha to verified unless the repo actually has evidence for it.

Examples:

- route renders != route verified
- partial close != terminal close
- a helpful read model != production execution support

### 3) Prefer read-first value

When choosing between:

- adding a truthful read-only view, or
- adding a half-proven write flow,

prefer the read-only view unless the write path is genuinely verified.

### 4) Keep public docs public-safe

Do not commit:

- private RPC endpoints
- API keys
- private wallet addresses unless explicitly intended and reviewed
- local-only workstation paths in public-facing docs
- raw personal artifacts from wallet prompts or browser sessions

Use placeholders like:

- `<owner-address>`
- `YOUR_API_KEY`
- `<capture-session>`

## Testing expectations

There is not a big formal test suite yet, so be explicit about what kind of change you made.

### For docs-only PRs

- check links
- check command names against the actual CLI
- keep public-safe placeholders

### For CLI/code PRs

At minimum, run:

```bash
./sigma --help
python3 -m compileall sigma_operator
```

If you changed a specific command, run that command’s help and a realistic non-destructive example too.

### For live-route truth changes

If you are claiming new live truth, document:

- what was verified
- what remains uncertain
- where the evidence lives

Usually that means touching `SIGMA_RUN_LEDGER.md` and either `STATUS.md` or a route-specific note.

## Good PR shapes

Strong examples:

- make README clearer without overselling
- improve decode/account output clarity
- tighten route-truth wording
- add a genuinely useful read-only surface
- reduce ambiguity between similar Sigma actions
- improve contributor orientation

Weak examples:

- broad marketing language without evidence
- giant speculative command surfaces
- execution support that depends on unverified wallet behavior
- governance-first framing that ignores the current repo truth

## Before opening a PR

Quick checklist:

- [ ] command names still match the actual CLI
- [ ] no secrets or personal artifacts were added
- [ ] public docs still reflect verified truth
- [ ] maturity labels still make sense
- [ ] examples remain read-safe unless explicitly documented otherwise

## Tone guide

Keep the repo clear, direct, and a little opinionated.

The best SigmaCLI contributions usually make the repo:

- easier to trust
- easier to read
- harder to misunderstand
