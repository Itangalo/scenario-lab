# Nodes left out of the readability pass (ECHO 2026-09-24)

Sentences about pathogens, outbreaks and biological weapons tripped a safety filter on the agents, so they were left out of the readability pass. This file lists where that happened, so those passages can be updated some other way. It names nodes only and quotes nothing.

## The six V2 nodes left out of the agent pass

The first V2 editor was stopped before it had made any edits, so these nodes were left out of the agent pass:

- `turn-08-V21`
- `option-10-V212`
- `turn-10-V212`
- `turn-11-V212`
- `turn-12-V212`
- `turn-13-V212`

Update (ECHO 2026-09-24): Claude has since edited their sentences that are not about biological threats in the main session. These are the reader's four issues (diplomats instead of the External Action Service, running models on European servers instead of inference, the Institute's cleared list explained, and research into model internals instead of an interpretability result), plus political capital and plain words for telemetry. Sentences about biological threats are still as they were. `turn-12-V212` consists almost entirely of such sentences and is unchanged.

## Nodes edited around untouched sentences

In these nodes everything was edited except the sentences a filter flagged as biological. The first figure is the number of such sentences left untouched. The filter is broad: many flagged sentences are harmless mentions, such as "detection, including for biological threats", which may not need any change. The second figure counts readability issues the readers found inside those sentences and that were skipped – that is where a known problem remains.

### Shared

- `option-02-1` – 1 untouched sentence
- `turn-01` – 1 untouched sentence

### A1

- `turn-04-A1` – 2 untouched sentences
- `turn-05-A1` – 2 untouched sentences
- `turn-09-A12` – 1 untouched sentence
- `turn-11-A122` – 1 untouched sentence
- `turn-12-A121` – 2 untouched sentences
- `turn-13-A111` – 3 untouched sentences
- `turn-13-A121` – 1 untouched sentence

### A2

- `option-06-A22` – 1 untouched sentence
- `option-10-A211` – 1 untouched sentence
- `option-10-A212` – 4 untouched sentences
- `turn-03-A2` – 7 untouched sentences
- `turn-05-A2` – 2 untouched sentences
- `turn-06-A21` – 1 untouched sentence
- `turn-07-A21` – 2 untouched sentences
- `turn-07-A22` – 1 untouched sentence
- `turn-09-A21` – 5 untouched sentences
- `turn-11-A222` – 1 untouched sentence
- `turn-12-A211` – 1 untouched sentence
- `turn-12-A212` – 3 untouched sentences
- `turn-13-A211` – 2 untouched sentences
- `turn-13-A212` – 1 untouched sentence
- `turn-13-A222` – 2 untouched sentences

### P1

- `option-10-P111` – 3 untouched sentences
- `option-10-P112` – 2 untouched sentences, 2 skipped issues
- `option-10-P121` – 4 untouched sentences, 2 skipped issues
- `option-10-P122` – 1 untouched sentence
- `turn-07-P11` – 5 untouched sentences, 2 skipped issues
- `turn-10-P111` – 2 untouched sentences
- `turn-10-P112` – 2 untouched sentences
- `turn-10-P121` – 3 untouched sentences
- `turn-10-P122` – 1 untouched sentence
- `turn-11-P111` – 1 untouched sentence
- `turn-11-P121` – 1 untouched sentence
- `turn-11-P122` – 5 untouched sentences, 2 skipped issues
- `turn-12-P111` – 6 untouched sentences
- `turn-12-P112` – 2 untouched sentences
- `turn-12-P121` – 2 untouched sentences
- `turn-13-P111` – 1 untouched sentence
- `turn-13-P112` – 5 untouched sentences, 2 skipped issues
- `turn-13-P121` – 4 untouched sentences
- `turn-13-P122` – 1 untouched sentence, 1 skipped issue

### P2

- `option-06-P22` – 1 untouched sentence
- `option-10-P211` – 3 untouched sentences
- `option-10-P212` – 3 untouched sentences, 1 skipped issue
- `turn-03-P2` – 4 untouched sentences
- `turn-10-P211` – 2 untouched sentences
- `turn-10-P212` – 2 untouched sentences
- `turn-11-P211` – 4 untouched sentences
- `turn-11-P212` – 1 untouched sentence
- `turn-12-P211` – 1 untouched sentence
- `turn-12-P212` – 1 untouched sentence
- `turn-13-P211` – 2 untouched sentences

### V1

- `option-06-V12` – 1 untouched sentence
- `option-10-V121` – 2 untouched sentences
- `option-10-V122` – 1 untouched sentence
- `turn-04-V1` – 6 untouched sentences
- `turn-05-V1` – 3 untouched sentences
- `turn-06-V11` – 1 untouched sentence
- `turn-06-V12` – 1 untouched sentence
- `turn-07-V11` – 6 untouched sentences
- `turn-08-V11` – 1 untouched sentence
- `turn-09-V12` – 1 untouched sentence
- `turn-10-V121` – 1 untouched sentence
- `turn-12-V111` – 5 untouched sentences
- `turn-13-V111` – 2 untouched sentences
- `turn-13-V112` – 3 untouched sentences
- `turn-13-V121` – 3 untouched sentences

### V2

- `turn-08-V22` – 3 untouched sentences
- `turn-09-V21` – 1 untouched sentence
- `turn-09-V22` – 1 untouched sentence, 1 skipped issue
- `turn-10-V211` – 3 untouched sentences
- `turn-11-V211` – 2 untouched sentences
- `turn-11-V222` – 1 untouched sentence
- `turn-12-V211` – 2 untouched sentences
- `turn-13-V211` – 2 untouched sentences
- `turn-13-V221` – 2 untouched sentences

## Known problems that have been fixed

Update (ECHO 2026-09-24): of the readability issues the readers found inside biological sentences, three were fixed in later rounds and three more by word-level edits in the main session (`turn-13-P112`, `option-10-P121`, `turn-11-P122`). One, a reminder in `option-10-P112`, was left because it pushed the node over the length limit. `option-06-P22` ("weight security") and `turn-06-P21` ("close too") are fixed as well.

## Ways to update what remains

- By hand: Johan, or Claude working directly in the main session, sentence by sentence.
- Most flagged sentences probably need nothing; they are harmless mentions the broad filter caught.

