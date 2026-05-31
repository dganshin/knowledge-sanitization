# AGENTS

Repository-level instructions for future coding agents working in this repo.

## Execution environment workflow

- This repository follows a split workflow:
  - local Windows/macOS machine for code edits, review, and Git operations;
  - remote Linux GPU host (for example AutoDL or similar cloud platforms) for pulling code and running training/evaluation jobs.
- Do not assume the machine used for editing code is the same machine used for executing experiments.
- Prefer doing code-only changes while GPU resources are not being billed unnecessarily:
  - use a no-GPU/local editing mode when available; or
  - stop or avoid renting GPU compute before making standalone code edits, then push the changes and restart/sync on the remote execution host only when ready to run.
- After local code changes are completed, push them to GitHub and then instruct the user to pull the updated branch on the remote Linux server before rerunning jobs.
- When giving run instructions, distinguish clearly between:
  - local repository maintenance steps (`git add`, `git commit`, `git push`);
  - remote execution steps (`git pull`/`git fetch`, environment activation, training/evaluation commands).

## Git workflow

- When you modify code or scripts at the user's request, push the change to the remote branch unless the user explicitly says not to.
- After pushing, remind the user to pull on the server before rerunning jobs.
- If you rewrote branch history, do not suggest a normal `git pull` as the default. Tell the user to sync with a command that matches the rewrite, for example `git fetch` plus `git reset --hard origin/<branch>`.

## Commit hygiene

- Do not create many tiny commits for closely related edits.
- If the latest local/remote commit(s) are small follow-up fixes to the same task, prefer folding them into the previous commit with `git commit --amend` or by squashing before pushing.
- If two recent commits touch the same file and belong to the same logical change, prefer merging them into one clean commit.
- Use a new commit only when the change is meaningfully separate, when preserving intermediate history matters, or when the user explicitly asks to keep commits separate.

## Scope discipline

- For "just fix the error" requests, keep edits minimal and avoid opportunistic refactors.
- When making a minimal fix, state clearly what was changed and what known risks remain.
