# Decisions log

One dated entry per chat that decided something. Newest first. Record the
decision and the reason, not the whole conversation.

## 2026-11-24: Prompt versioning deferred

- Decision: don't add prompt versioning or a prompt registry yet.
- Reason: the code has no LLM calls yet. Prompts first appear in Plan 3
  (LLM question drafting) and Plan 5 (generation, E4).
- When prompts arrive: keep them as template files in `prompts/` in Git, and
  record the prompt name, its commit or content hash, the model ID and the
  settings in every results file. Add a tool such as Langfuse or LangSmith only
  if many prompt variants or A/B tests are run.

## 2026-11-24: Cross-chat context

- Decision: keep shared context in `CLAUDE.md`, which every session loads
  automatically, and keep history in this file.
- Reason: full chat transcripts are not loaded automatically and would fill
  the context window. A short summary of decisions does the job.
