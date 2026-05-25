# Reproduction Status

## Current Status

- LLaMA-7B based training and evaluation pipeline has been reproduced at the repository level.
- The current LoRA result is a smoke test result, not a final paper-level reproduction result.
- The main blocker is no longer environment setup or GPU placement.
- The current blocker is the cost of full retain evaluation on `K_R = 17921`.

## Confirmed Facts

### Model And Environment

- HF-format `LLaMA-7B` can be loaded successfully.
- The `ks310` environment is usable on the Linux server.
- Training and evaluation can both run on the server GPU.

### Pipeline

- LoRA training can complete.
- Adapter files can be saved.
- Evaluation can produce metrics.
- Lightweight text summaries can be exported into the repository.

### GPU Usage

- Evaluation previously had a bug where the model could silently stay on CPU.
- That issue has been fixed.
- Evaluation now prints:
  - `Model param device: cuda:0`
  - `Eval device: cuda:0`
- If the model is not on CUDA, evaluation now fails fast instead of silently running on CPU.

## Current LoRA Smoke Test Result

- `K_F = 0.43478260869565216`
- `K_S = 0.08695652173913043`
- `K_R = 0.4876959991071927`

### Interpretation

- This result is valid as a smoke test result.
- It proves:
  - training works
  - evaluation works
  - LoRA adapters are active
- It does not yet prove paper-level reproduction success.

## Why `K_F/K_S` Are Small While `K_R` Is Large

This is by design in the dataset protocol.

- `K_F` evaluates only the small set of forget targets.
- `K_S` evaluates the same forget targets for sanitization phrase behavior.
- `K_R` evaluates the large retain set.

So the asymmetry is expected:

- `K_F`: about 23 examples
- `K_S`: about 23 examples
- `K_R`: 17921 examples

This is not a path bug or a loading bug.

## Main Bottleneck

Training itself is not the dominant cost.

The dominant cost is full generative evaluation on:

- `Orig K_R = 17921`
- `LoRA K_R = 17921`

Even after fixing GPU placement, measured evaluation behavior is still expensive:

- `EVAL_BATCH_SIZE = 2`
- about `20GB` GPU memory usage
- about `96% - 97%` GPU utilization
- about `3.4s` per sample on the large retain set

This implies:

- one full `K_R = 17921` evaluation can take about `17h`
- repeated full evaluation is not practical during tuning

## Current Assessment Of The LoRA Result

Without relying on `Orig`, the current LoRA result already suggests:

1. `K_R` is not obviously collapsed.
2. `K_F` is still too high.
3. `K_S` is too low.

This means the model appears to have been perturbed, but it has not yet learned a stable sanitization behavior.

## Recommended Evaluation Strategy

Do not keep using full evaluation during tuning.

Use a two-stage strategy instead.

### Stage A: Low-Cost Tuning Evaluation

- `K_F`: full
- `K_S`: full
- `K_R`: sampled, e.g. 500 or 1000

### Stage B: Final Full Evaluation

- Run full `K_R = 17921` only for the most promising final configuration(s).

## Recommended Immediate Next Steps

1. Run low-cost `Orig` only on:
   - `Orig K_F`
   - `Orig K_S`
2. Export all current LoRA outputs on the 23 forget examples.
3. Use stronger training, but evaluate only:
   - `K_F` full
   - `K_S` full
   - `K_R` sampled
4. Run full `K_R` only after `K_F` clearly drops and `K_S` clearly rises.

## What Not To Do Now

- Do not run full `Orig K_R = 17921` right now.
- Do not run full evaluation after every tuning attempt.
- Do not change answer-only loss yet.
- Do not switch models yet.
- Do not switch from beam search to greedy search for the main reproduction path.

## Practical Project Positioning

The most accurate current project description is:

> We have completed repository-level reproduction of the LLaMA-7B training and evaluation pipeline, and obtained a valid LoRA smoke test result. The main blocker is no longer environment setup, but the cost of full generative retain evaluation. The next stage should use low-cost tuning evaluation with full `K_F/K_S` and sampled `K_R`, and reserve full `K_R` evaluation for only the most promising final configurations.
