# CHANGELOG: draft revised annotations (second pass)

Drop-in files: `revised/annotations/<id>_motion.json` (same schema as the originals: `json.dumps(indent=2)` + newline, same `dataset`/`fps`/`source`, his raw label words, 0.5 s timestamp grid). Frames are `mmss_to_frame(t, 29.97)`. Every original segment appears exactly once below. Machine-readable versions: `changes.csv` (one row per original segment plus one per new segment) and `changes_steps.csv` (every individual edit, in order).

Change types: **relabel** (label changed; frames may also have been trimmed or merged), **boundary_trim** (same label, trimmed inward to the steady part), **split** (kept only the clear sub-parts), **merged** (absorbed into a neighbour with the same label after a relabel), **new_from_gap** / **new_event_in_segment** (new segments), **removed** (left unlabelled), **unchanged**. `flagged` = transition kept unchanged (rule 3) whose from/to state neighbour no longer sits next to it.

## 0066 (10_fish): 43 revised segments (from 54); {'unchanged': 28, 'relabel': 13, 'boundary_trim': 6, 'merged': 5, 'removed': 2, 'new_event_in_segment': 1, 'new_from_gap': 1}

### relabel (13)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 10 | traveling to compaction 8287-8317 | traveling 6938-9755 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.9, M 0.1, dlogR -0.06 |
| 11 | compaction 8317-8377 | traveling 6938-9755 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.29/s (thr 0.20), dlogR -0.37, dur 2.0s, P mean 0.82 min 0.75 (pre 0.90), 100% frames P>=0.65, speed x1.62 | P 0.82, M 0.15, dlogR -0.33 |
| 12 | compaction to traveling 8377-8407 | traveling 6938-9755 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.85, M 0.05, dlogR -0.01 |
| 17 | shoaling 12932-13352 | compaction 13067-13127 (remnants < 2 s left unlabelled) | split around new compaction 13067-13127 / weak shoaling: steady 48%, no other state >= 60% (traveling 0%); P 0.41, M 0.20 -> leave unlabelled / weak shoaling: steady 2%, no other state >= 60% (milling 19%); P 0.37, M 0.39 -> leave unlabelled | P 0.37, M 0.33, dlogR -0.23 |
| 24 | traveling to compaction 15090-15120 | traveling 14655-15180 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.86, M 0.12, dlogR -0.07 |
| 25 | compaction 15120-15180 | traveling 14655-15180 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.17/s (thr 0.20), dlogR -0.25, dur 2.0s, P mean 0.75 min 0.68 (pre 0.86), 100% frames P>=0.65, speed x1.04 | P 0.75, M 0.18, dlogR -0.24 |
| 26 | compaction to shoaling 15180-15225 | traveling to shoaling 15180-15225 | transition renamed because neighbour was relabelled / transition kept as is (rule 3) but its 'to' state segment is not adjacent any more (trimmed/removed neighbour or original gap) | P 0.62, M 0.21, dlogR -0.05 |
| 37 | traveling to compaction 19510-19540 | traveling 19436-19585 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.83, M 0.2, dlogR -0.08 |
| 38 | compaction 19540-19585 | traveling 19436-19585 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.17/s (thr 0.20), dlogR -0.21, dur 1.5s, P mean 0.86 min 0.74 (pre 0.83), 100% frames P>=0.65, speed x1.26 | P 0.86, M 0.2, dlogR -0.19 |
| 39 | compaction to shoaling 19585-19645 | traveling to shoaling 19585-19645 | transition renamed because neighbour was relabelled | P 0.65, M 0.41, dlogR -0.14 |
| 41 | shoaling to compaction 19735-19795 | shoaling to traveling 19735-19795 | transition renamed because neighbour was relabelled | P 0.69, M 0.06, dlogR 0.13 |
| 42 | compaction 19795-19885 | traveling 19795-22882 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.21/s (thr 0.20), dlogR -0.38, dur 3.0s, P mean 0.96 min 0.92 (pre 0.85), 100% frames P>=0.65, speed x3.15 | P 0.96, M 0.08, dlogR -0.36 |
| 43 | compaction to traveling 19885-19915 | traveling 19795-22882 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.98, M 0.21, dlogR 0.07 |

### boundary_trim (6)

| old_seg | old | new | trimmed_s | reason | metrics |
|---|---|---|---|---|---|
| 2 | milling 944-1244 | milling 959-1244 | 0.5 | trimmed to steady milling (M>=0.50 & P<=0.50 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.53/0.67 .. 0.17/0.76 | P 0.28, M 0.77, dlogR -0.43 |
| 15 | traveling 11194-12842 | traveling 11194-12812 | 1.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.76/0.11 .. 0.73/0.27 | P 0.89, M 0.14, dlogR 0.12 |
| 35 | traveling 18731-19301 | traveling 18731-19286 | 0.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.76/0.29 .. 0.63/0.09 | P 0.89, M 0.19, dlogR 0.03 |
| 40 | shoaling 19645-19735 | shoaling 19660-19735 | 0.5 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.49/0.35 .. 0.31/0.09 | P 0.28, M 0.25, dlogR 0.15 |
| 49 | traveling 23946-24096 | traveling 23976-24096 | 1.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +30 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.63/0.12 .. 0.97/0.07 | P 0.79, M 0.22, dlogR 0.18 |
| 53 | traveling 24321-24578 | traveling 24321-24560 | 0.6 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -18 fr (-0.6s); edge P/M before trim 0.76/0.14 .. 0.44/0.12 | P 0.93, M 0.16, dlogR 0.26 |

### merged (5)

| old_seg | old | new | merged_with_orig | reason | metrics |
|---|---|---|---|---|---|
| 9 | traveling 6938-8287 | traveling 6938-9755 | 10;11;12;13 | absorbed into a same-label neighbour after an adjacent relabel | P 0.89, M 0.16, dlogR -0.27 |
| 13 | traveling 8407-9755 | traveling 6938-9755 | 9;10;11;12 | absorbed into a same-label neighbour after an adjacent relabel | P 0.92, M 0.19, dlogR 0.8 |
| 23 | traveling 14655-15090 | traveling 14655-15180 | 24;25 | absorbed into a same-label neighbour after an adjacent relabel | P 0.78, M 0.2, dlogR -0.02 |
| 36 | traveling 19436-19510 | traveling 19436-19585 | 37;38 | absorbed into a same-label neighbour after an adjacent relabel | P 0.8, M 0.14, dlogR 0.12 |
| 44 | traveling 19915-22882 | traveling 19795-22882 | 42;43 | absorbed into a same-label neighbour after an adjacent relabel | P 0.9, M 0.17, dlogR -0.03 |

### new_from_gap (1)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| compaction | 07:47 | 07:49 | 13996-14056 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.34/s (thr 0.20), dlogR -0.42, dur 2.3s, P mean 0.32 min 0.15 (pre 0.51), 0% frames P>=0.65, speed x1.33; inside gap |

### new_event_in_segment (1)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| compaction | 07:16 | 07:18 | 13067-13127 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.42/s (thr 0.20), dlogR -0.69, dur 2.8s, P mean 0.28 min 0.11 (pre 0.47), 0% frames P>=0.65, speed x1.77; carved from shoaling |

### removed (2)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 27 | shoaling 15225-15794 | —  | weak shoaling: steady 21%, no other state >= 60% (traveling 17%); P 0.53, M 0.14 -> leave unlabelled | P 0.53, M 0.14, dlogR -0.16 |
| 47 | milling 23481-23631 | —  | weak milling: steady 44%, no clear run >= 2.0s after grid snap; P 0.37, M 0.51 | P 0.37, M 0.51, dlogR 0.33 |

### unchanged (28)

Segments: 0, 1, 3, 4, 5, 6, 7, 8, 14, 16, 18, 19, 20, 21, 22, 28, 29, 30, 31, 32, 33, 34, 45, 46, 48, 50, 51, 52.

Flagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): 16 (traveling to shoaling), 18 (shoaling to traveling), 28 (shoaling to traveling), 46 (traveling to milling), 48 (milling to traveling).

## 0084 (30_fish): 70 revised segments (from 110); {'unchanged': 47, 'relabel': 38, 'merged': 13, 'boundary_trim': 9, 'removed': 3, 'new_event_in_segment': 1}

### relabel (38)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 6 | expansion to compaction 1379-1454 | expansion to traveling 1379-1454 | transition renamed because neighbour was relabelled | P 0.67, M 0.16, dlogR 0.05 |
| 7 | compaction 1454-1513 | traveling 1454-2502 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.20/s (thr 0.17), dlogR -0.28, dur 2.0s, P mean 0.91 min 0.88 (pre 0.83), 100% frames P>=0.65, speed x1.52 | P 0.91, M 0.05, dlogR -0.27 |
| 8 | compaction to traveling 1513-1543 | traveling 1454-2502 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.95, M 0.03, dlogR 0.04 |
| 10 | traveling to compaction 1933-1963 | traveling 1454-2502 | no state change left after neighbour relabel; 80% frames steady traveling | P 0.68, M 0.23, dlogR -0.06 |
| 11 | compaction 1963-2113 | traveling 1454-2502 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.21/s (thr 0.17), dlogR -0.56, dur 5.0s, P mean 0.79 min 0.68 (pre 0.68), 100% frames P>=0.65, speed x1.51 | P 0.79, M 0.13, dlogR -0.56 |
| 12 | compaction to expansion 2113-2143 | traveling 1454-2502 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.71, M 0.39, dlogR 0.08 |
| 13 | expansion 2143-2218 | traveling 1454-2502 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.29/s (thr 0.17), dlogR +0.55, dur 2.5s, P mean 0.74 min 0.67 (pre 0.71), 100% frames P>=0.65, speed x1.70 | P 0.74, M 0.44, dlogR 0.53 |
| 14 | expansion to traveling 2218-2248 | traveling 1454-2502 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.89, M 0.3, dlogR -0.01 |
| 16 | compaction 2682-2877 | traveling 2682-4555 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.21/s (thr 0.17), dlogR -0.79, dur 6.5s, P mean 0.92 min 0.86 (pre 0.76), 100% frames P>=0.65, speed x2.16 | P 0.92, M 0.11, dlogR -0.77 |
| 17 | compaction to traveling 2877-2907 | traveling 2682-4555 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.85, M 0.09, dlogR -0.03 |
| 19 | traveling to compaction 4346-4361 | traveling 2682-4555 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.94, M 0.04, dlogR -0.02 |
| 20 | compaction 4361-4481 | traveling 2682-4555 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.13/s (thr 0.17), dlogR -0.36, dur 4.0s, P mean 0.92 min 0.87 (pre 0.93), 100% frames P>=0.65, speed x1.58 | P 0.92, M 0.04, dlogR -0.35 |
| 21 | compaction to traveling 4481-4510 | traveling 2682-4555 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.89, M 0.04, dlogR 0.0 |
| 34 | compaction 8332-8422 | traveling 8332-8422 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.22/s (thr 0.17), dlogR -0.45, dur 3.0s, P mean 0.73 min 0.66 (pre 0.69), 100% frames P>=0.65, speed x1.32 | P 0.73, M 0.08, dlogR -0.44 |
| 35 | compaction to shoaling 8422-8452 | traveling to shoaling 8422-8452 | transition renamed because neighbour was relabelled | P 0.57, M 0.1, dlogR -0.01 |
| 49 | traveling to compaction 11928-11958 | traveling 11778-12123 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.91, M 0.04, dlogR -0.05 |
| 50 | compaction 11958-12123 | traveling 11778-12123 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.18/s (thr 0.17), dlogR -0.59, dur 5.5s, P mean 0.85 min 0.71 (pre 0.91), 100% frames P>=0.65, speed x0.76 | P 0.85, M 0.14, dlogR -0.58 |
| 52 | traveling to compaction 13037-13052 | traveling 12348-13172 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.89, M 0.2, dlogR -0.02 |
| 53 | compaction 13052-13172 | traveling 12348-13172 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.22/s (thr 0.17), dlogR -0.59, dur 4.0s, P mean 0.86 min 0.71 (pre 0.87), 100% frames P>=0.65, speed x1.04 | P 0.86, M 0.13, dlogR -0.57 |
| 56 | traveling to compaction 13382-13397 | traveling 13247-14026 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.75, M 0.15, dlogR 0.06 |
| 57 | compaction 13397-13472 | traveling 13247-14026 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.26/s (thr 0.17), dlogR -0.47, dur 2.5s, P mean 0.93 min 0.82 (pre 0.77), 100% frames P>=0.65, speed x3.43 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.94, M 0.05, dlogR -0.45 |
| 58 | compaction to traveling 13472-13501 | traveling 13247-14026 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.98, M 0.04, dlogR -0.02 |
| 60 | traveling to compaction 13576-13591 | traveling 13247-14026 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.98, M 0.04, dlogR -0.01 |
| 61 | compaction 13591-13681 | traveling 13247-14026 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.13/s (thr 0.17), dlogR -0.24, dur 3.0s, P mean 0.92 min 0.82 (pre 0.98), 100% frames P>=0.65, speed x0.61 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.92, M 0.08, dlogR -0.23 |
| 62 | compaction to traveling 13681-13711 | traveling 13247-14026 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.79, M 0.27, dlogR -0.0 |
| 64 | traveling to compaction 13876-13906 | traveling 13247-14026 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.82, M 0.07, dlogR -0.06 |
| 65 | compaction 13906-14041 | traveling 13247-14026 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.21/s (thr 0.17), dlogR -0.66, dur 4.5s, P mean 0.74 min 0.64 (pre 0.82), 95% frames P>=0.65, speed x1.33 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.74, M 0.2, dlogR -0.65 |
| 66 | compaction to shoaling 14041-14101 | traveling to shoaling 14041-14101 | transition renamed because neighbour was relabelled | P 0.51, M 0.17, dlogR 0.05 |
| 71 | traveling to compaction 16244-16274 | traveling 15959-16364 | no state change left after neighbour relabel; 100% frames steady traveling / split around new expansion 15809-15959 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.89/0.07 .. 0.62/0.33 | P 0.94, M 0.12, dlogR -0.03 |
| 72 | compaction 16274-16379 | traveling 15959-16364 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.24/s (thr 0.17), dlogR -0.51, dur 3.5s, P mean 0.80 min 0.62 (pre 0.94), 97% frames P>=0.65, speed x1.17 / split around new expansion 15809-15959 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.89/0.07 .. 0.62/0.33 | P 0.8, M 0.22, dlogR -0.5 |
| 76 | expansion to compaction 17098-17128 | expansion to traveling 17098-17128 | transition renamed because neighbour was relabelled | P 0.91, M 0.08, dlogR -0.11 |
| 77 | compaction 17128-17368 | traveling 17128-17592 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.20/s (thr 0.17), dlogR -0.74, dur 8.0s, P mean 0.91 min 0.84 (pre 0.91), 100% frames P>=0.65, speed x1.13 | P 0.91, M 0.07, dlogR -0.73 |
| 78 | compaction to traveling 17368-17398 | traveling 17128-17592 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.94, M 0.1, dlogR 0.08 |
| 89 | traveling to expansion 20290-20305 | traveling 19391-21009 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.73, M 0.38, dlogR 0.03 |
| 90 | expansion 20305-20380 | traveling 19391-21009 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.22/s (thr 0.17), dlogR +0.40, dur 2.5s, P mean 0.81 min 0.73 (pre 0.74), 100% frames P>=0.65, speed x2.30 | P 0.81, M 0.2, dlogR 0.38 |
| 91 | expansion to compaction 20380-20410 | traveling 19391-21009 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.92, M 0.18, dlogR -0.02 |
| 92 | compaction 20410-20484 | traveling 19391-21009 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.33/s (thr 0.17), dlogR -0.47, dur 2.5s, P mean 0.96 min 0.95 (pre 0.92), 100% frames P>=0.65, speed x3.15 | P 0.96, M 0.07, dlogR -0.45 |
| 93 | compaction to traveling 20484-20514 | traveling 19391-21009 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.97, M 0.03, dlogR -0.04 |

### boundary_trim (9)

| old_seg | old | new | trimmed_s | reason | metrics |
|---|---|---|---|---|---|
| 0 | traveling 0-360 | traveling 0-345 | 0.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.85/0.13 .. 0.57/0.38 | P 0.91, M 0.13, dlogR -0.25 |
| 30 | shoaling 5305-5380 | shoaling 5305-5350 | 1.0 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.31/0.26 .. 0.38/0.06 | P 0.34, M 0.1, dlogR 0.07 |
| 67 | shoaling 14101-14251 | shoaling 14101-14206 | 1.5 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.37/0.16 .. 0.42/0.07 | P 0.3, M 0.21, dlogR 0.28 |
| 69 | traveling 14371-15749 | traveling 14371-15599 | 5.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -150 fr (-5.0s); edge P/M before trim 0.77/0.18 .. 0.68/0.24 | P 0.86, M 0.17, dlogR 0.31 |
| 83 | traveling 18012-18342 | traveling 18057-18342 | 1.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.65/0.02 .. 0.70/0.46 | P 0.73, M 0.18, dlogR 0.4 |
| 84 | traveling 18491-19151 | traveling 18506-19151 | 0.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.63/0.39 .. 0.66/0.08 | P 0.73, M 0.22, dlogR -0.17 |
| 86 | shoaling 19226-19331 | shoaling 19271-19331 | 1.5 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.47/0.06 .. 0.18/0.09 | P 0.29, M 0.08, dlogR 0.07 |
| 107 | milling 23526-24276 | milling 23661-23796 | 20.5 | weak milling (steady 31%; P 0.42, M 0.47): kept only the clear part(s) | P 0.42, M 0.47, dlogR -0.06 |
| 109 | shoaling 24396-24593 | shoaling 24396-24441 | 5.1 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +0 fr (+0.0s), end -152 fr (-5.1s); edge P/M before trim 0.36/0.22 .. 0.16/0.17 | P 0.26, M 0.38, dlogR 0.11 |

### merged (13)

| old_seg | old | new | merged_with_orig | reason | metrics |
|---|---|---|---|---|---|
| 9 | traveling 1543-1933 | traveling 1454-2502 | 7;8;10;11;12;13;14;15 | absorbed into a same-label neighbour after an adjacent relabel | P 0.78, M 0.26, dlogR 0.13 |
| 15 | traveling 2248-2502 | traveling 1454-2502 | 7;8;9;10;11;12;13;14 | absorbed into a same-label neighbour after an adjacent relabel | P 0.88, M 0.15, dlogR -0.11 |
| 18 | traveling 2907-4346 | traveling 2682-4555 | 16;17;19;20;21;22 | absorbed into a same-label neighbour after an adjacent relabel | P 0.88, M 0.15, dlogR 0.61 |
| 22 | traveling 4510-4555 | traveling 2682-4555 | 16;17;18;19;20;21 | absorbed into a same-label neighbour after an adjacent relabel | P 0.84, M 0.08, dlogR -0.09 |
| 48 | traveling 11778-11928 | traveling 11778-12123 | 49;50 | absorbed into a same-label neighbour after an adjacent relabel | P 0.94, M 0.05, dlogR 0.32 |
| 51 | traveling 12348-13037 | traveling 12348-13172 | 52;53 | absorbed into a same-label neighbour after an adjacent relabel | P 0.77, M 0.11, dlogR 0.29 |
| 55 | traveling 13202-13382 | traveling 13247-14026 | 56;57;58;59;60;61;62;63;64;65 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.74, M 0.13, dlogR 0.45 |
| 59 | traveling 13501-13576 | traveling 13247-14026 | 55;56;57;58;60;61;62;63;64;65 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.98, M 0.03, dlogR -0.02 |
| 63 | traveling 13711-13876 | traveling 13247-14026 | 55;56;57;58;59;60;61;62;64;65 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end -15 fr (-0.5s); edge P/M before trim 0.59/0.24 .. 0.64/0.19 | P 0.72, M 0.42, dlogR 0.46 |
| 70 | traveling 15914-16244 | traveling 15959-16364 | 71;72 | split around new expansion 15809-15959 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.89/0.07 .. 0.62/0.33 | P 0.9, M 0.15, dlogR 0.01 |
| 79 | traveling 17398-17592 | traveling 17128-17592 | 77;78 | absorbed into a same-label neighbour after an adjacent relabel | P 0.85, M 0.08, dlogR -0.18 |
| 88 | traveling 19391-20290 | traveling 19391-21009 | 89;90;91;92;93;94 | absorbed into a same-label neighbour after an adjacent relabel | P 0.84, M 0.1, dlogR -0.16 |
| 94 | traveling 20514-21009 | traveling 19391-21009 | 88;89;90;91;92;93 | absorbed into a same-label neighbour after an adjacent relabel | P 0.86, M 0.15, dlogR -0.03 |

### new_event_in_segment (1)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| expansion | 08:47.5 | 08:52.5 | 15809-15959 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.19/s (thr 0.17), dlogR +0.71, dur 5.1s, P mean 0.61 min 0.39 (pre 0.52), 45% frames P>=0.65, speed x1.46; carved from traveling |

### removed (3)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 33 | traveling to compaction 8317-8332 | —  | transition traveling->traveling after neighbour relabel; only 33% steady | P 0.65, M 0.08, dlogR 0.0 |
| 54 | compaction to traveling 13172-13202 | —  | transition traveling->traveling after neighbour relabel; only 50% steady | P 0.66, M 0.25, dlogR 0.0 |
| 81 | shoaling 17652-17862 | —  | weak shoaling: steady 2%, no other state >= 60% (traveling 0%); P 0.48, M 0.06 -> leave unlabelled | P 0.48, M 0.06, dlogR 0.2 |

### unchanged (47)

Segments: 1, 2, 3, 4, 5, 23, 24, 25, 26, 27, 28, 29, 31, 32, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 68, 73, 74, 75, 80, 82, 85, 87, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 108.

Flagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): 3 (compaction), 75 (expansion), 80 (traveling to shoaling), 82 (shoaling to traveling), 108 (milling to shoaling).

## 0103 (70_fish): 105 revised segments (from 152); {'unchanged': 74, 'relabel': 36, 'merged': 18, 'boundary_trim': 13, 'removed': 11, 'new_from_gap': 2}

### relabel (36)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 7 | traveling to compaction 854-869 | traveling 809-959 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.70/0.05 .. 0.56/0.17 | P 0.77, M 0.02, dlogR -0.01 |
| 8 | compaction 869-1004 | traveling 809-959 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.11/s (thr 0.08), dlogR -0.38, dur 4.5s, P mean 0.75 min 0.56 (pre 0.76), 90% frames P>=0.65, speed x1.31 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.70/0.05 .. 0.56/0.17 | P 0.75, M 0.08, dlogR -0.37 |
| 12 | traveling to compaction 1528-1558 | traveling 1334-1723 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.94, M 0.08, dlogR -0.04 |
| 13 | compaction 1558-1723 | traveling 1334-1723 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.14/s (thr 0.08), dlogR -0.48, dur 5.5s, P mean 0.81 min 0.65 (pre 0.94), 99% frames P>=0.65, speed x0.74 | P 0.81, M 0.12, dlogR -0.47 |
| 34 | traveling to compaction 4690-4720 | traveling 4496-5155 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.84/0.28 .. 0.62/0.16 | P 0.7, M 0.45, dlogR -0.0 |
| 35 | compaction 4720-4840 | traveling 4496-5155 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.09/s (thr 0.08), dlogR -0.23, dur 4.0s, P mean 0.84 min 0.73 (pre 0.70), 100% frames P>=0.65, speed x1.46 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.84/0.28 .. 0.62/0.16 | P 0.84, M 0.31, dlogR -0.23 |
| 36 | compaction to traveling 4840-4885 | traveling 4496-5155 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.84/0.28 .. 0.62/0.16 | P 0.9, M 0.19, dlogR -0.02 |
| 38 | traveling to compaction 4960-4990 | traveling 4496-5155 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.84/0.28 .. 0.62/0.16 | P 0.89, M 0.11, dlogR -0.02 |
| 39 | compaction 4990-5230 | traveling 4496-5155 | strict exp/comp: -> traveling (not rapid; 78% frames steady traveling); peak dlogR/dt 0.08/s (thr 0.08), dlogR -0.38, dur 8.0s, P mean 0.75 min 0.61 (pre 0.89), 78% frames P>=0.65, speed x0.90 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.84/0.28 .. 0.62/0.16 | P 0.75, M 0.09, dlogR -0.37 |
| 42 | traveling to compaction 5934-5964 | traveling 5395-6234 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +120 fr (+4.0s), end -75 fr (-2.5s); edge P/M before trim 0.51/0.11 .. 0.25/0.11 | P 0.92, M 0.13, dlogR -0.03 |
| 43 | compaction 5964-6309 | traveling 5395-6234 | strict exp/comp: -> traveling (not rapid; 79% frames steady traveling); peak dlogR/dt 0.09/s (thr 0.08), dlogR -0.60, dur 11.5s, P mean 0.73 min 0.25 (pre 0.92), 79% frames P>=0.65, speed x1.00 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +120 fr (+4.0s), end -75 fr (-2.5s); edge P/M before trim 0.51/0.11 .. 0.25/0.11 | P 0.73, M 0.09, dlogR -0.6 |
| 44 | compaction to shoaling 6309-6354 | traveling to shoaling 6309-6354 | transition renamed because neighbour was relabelled | P 0.24, M 0.12, dlogR -0.02 |
| 64 | traveling to compaction 9815-9845 | traveling 9590-10235 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.84/0.05 .. 0.63/0.22 | P 0.9, M 0.03, dlogR -0.0 |
| 65 | compaction 9845-10010 | traveling 9590-10235 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.08), dlogR -0.42, dur 5.5s, P mean 0.83 min 0.78 (pre 0.90), 100% frames P>=0.65, speed x0.91 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.84/0.05 .. 0.63/0.22 | P 0.83, M 0.06, dlogR -0.41 |
| 66 | compaction to traveling 10010-10055 | traveling 9590-10235 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.84/0.05 .. 0.63/0.22 | P 0.81, M 0.03, dlogR -0.02 |
| 79 | traveling to compaction 12168-12183 | traveling 11958-12557 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -165 fr (-5.5s); edge P/M before trim 0.87/0.27 .. 0.62/0.37 | P 0.89, M 0.03, dlogR 0.01 |
| 80 | compaction 12183-12318 | traveling 11958-12557 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.09/s (thr 0.08), dlogR -0.19, dur 4.5s, P mean 0.90 min 0.85 (pre 0.90), 100% frames P>=0.65, speed x1.12 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -165 fr (-5.5s); edge P/M before trim 0.87/0.27 .. 0.62/0.37 | P 0.9, M 0.06, dlogR -0.19 |
| 81 | compaction to traveling 12318-12348 | traveling 11958-12557 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -165 fr (-5.5s); edge P/M before trim 0.87/0.27 .. 0.62/0.37 | P 0.94, M 0.03, dlogR -0.03 |
| 88 | shoaling to expansion 13906-13936 | shoaling 13786-14041 | no state change left after neighbour relabel; 100% frames steady shoaling / trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.30/0.28 .. 0.45/0.25 | P 0.14, M 0.27, dlogR 0.04 |
| 89 | expansion 13936-14071 | shoaling 13786-14041 | strict exp/comp: -> shoaling (not rapid; 82% frames steady shoaling); peak dlogR/dt 0.08/s (thr 0.08), dlogR +0.27, dur 4.5s, P mean 0.30 min 0.12 (pre 0.14), 0% frames P>=0.65, speed x1.34 / trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.30/0.28 .. 0.45/0.25 | P 0.3, M 0.27, dlogR 0.27 |
| 90 | expansion to traveling 14071-14266 | shoaling to traveling 14071-14266 | transition renamed because neighbour was relabelled | P 0.52, M 0.2, dlogR -0.03 |
| 96 | traveling to compaction 15854-15884 | traveling 15105-15989 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.67/0.16 .. 0.63/0.25 | P 0.89, M 0.12, dlogR -0.03 |
| 97 | compaction 15884-16004 | traveling 15105-15989 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.08/s (thr 0.08), dlogR -0.19, dur 4.0s, P mean 0.76 min 0.63 (pre 0.89), 95% frames P>=0.65, speed x0.90 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.67/0.16 .. 0.63/0.25 | P 0.76, M 0.18, dlogR -0.18 |
| 98 | compaction to expansion 16004-16064 | traveling to expansion 16004-16064 | transition renamed because neighbour was relabelled | P 0.59, M 0.34, dlogR 0.03 |
| 112 | traveling to compaction 18012-18042 | traveling 17802-18147 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.91/0.15 .. 0.55/0.40 | P 0.91, M 0.08, dlogR -0.01 |
| 113 | compaction 18042-18162 | traveling 17802-18147 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.08), dlogR -0.28, dur 4.0s, P mean 0.77 min 0.55 (pre 0.91), 88% frames P>=0.65, speed x0.86 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.91/0.15 .. 0.55/0.40 | P 0.77, M 0.22, dlogR -0.28 |
| 116 | compaction 18566-18731 | traveling 18566-18836 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.08), dlogR -0.40, dur 5.5s, P mean 0.78 min 0.65 (pre 0.63), 100% frames P>=0.65, speed x1.21 | P 0.78, M 0.07, dlogR -0.39 |
| 117 | compaction to traveling 18731-18776 | traveling 18566-18836 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.75, M 0.08, dlogR -0.07 |
| 123 | traveling to compaction 19930-19960 | traveling 19780-20185 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.72/0.40 .. 0.61/0.03 | P 0.86, M 0.1, dlogR -0.02 |
| 124 | compaction 19960-20260 | traveling 19780-20185 | strict exp/comp: -> traveling (not rapid; 78% frames steady traveling); peak dlogR/dt 0.08/s (thr 0.08), dlogR -0.47, dur 10.0s, P mean 0.73 min 0.53 (pre 0.86), 78% frames P>=0.65, speed x0.97 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.72/0.40 .. 0.61/0.03 | P 0.73, M 0.09, dlogR -0.46 |
| 133 | traveling to compaction 21189-21219 | traveling 20949-21459 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.88/0.03 .. 0.59/0.04 | P 0.9, M 0.17, dlogR -0.01 |
| 134 | compaction 21219-21339 | traveling 20949-21459 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.06/s (thr 0.08), dlogR -0.18, dur 4.0s, P mean 0.83 min 0.75 (pre 0.90), 100% frames P>=0.65, speed x0.81 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.88/0.03 .. 0.59/0.04 | P 0.83, M 0.15, dlogR -0.17 |
| 135 | compaction to traveling 21339-21369 | traveling 20949-21459 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.88/0.03 .. 0.59/0.04 | P 0.73, M 0.15, dlogR -0.03 |
| 145 | traveling to compaction 22732-22762 | traveling 22118-23392 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.77, M 0.1, dlogR -0.03 |
| 146 | compaction 22762-22882 | traveling 22118-23392 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.06/s (thr 0.08), dlogR -0.17, dur 4.0s, P mean 0.68 min 0.65 (pre 0.77), 98% frames P>=0.65, speed x1.08 | P 0.68, M 0.1, dlogR -0.17 |
| 147 | compaction to traveling 22882-22912 | traveling 22118-23392 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.68, M 0.12, dlogR 0.02 |

### boundary_trim (13)

| old_seg | old | new | trimmed_s | reason | metrics |
|---|---|---|---|---|---|
| 0 | traveling 0-420 | traveling 0-405 | 0.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.89/0.03 .. 0.64/0.18 | P 0.8, M 0.13, dlogR 0.01 |
| 19 | milling 2278-2622 | milling 2428-2577 | 6.5 | weak milling (steady 54%; P 0.17, M 0.51): kept only the clear part(s) | P 0.17, M 0.51, dlogR 0.07 |
| 27 | traveling 2997-3641 | traveling 3132-3641 | 4.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +135 fr (+4.5s), end +0 fr (+0.0s); edge P/M before trim 0.53/0.31 .. 0.78/0.05 | P 0.77, M 0.14, dlogR 0.2 |
| 45 | shoaling 6354-6578 | shoaling 6354-6503 | 2.5 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.18/0.20 .. 0.38/0.21 | P 0.31, M 0.22, dlogR 0.16 |
| 55 | traveling 8122-8931 | traveling 8167-8931 | 1.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.55/0.18 .. 0.83/0.03 | P 0.72, M 0.12, dlogR 0.26 |
| 83 | traveling 12947-13561 | traveling 12977-13561 | 1.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +30 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.59/0.23 .. 0.82/0.21 | P 0.84, M 0.07, dlogR 0.11 |
| 91 | traveling 14266-14745 | traveling 14266-14715 | 1.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.65/0.26 .. 0.66/0.14 | P 0.81, M 0.22, dlogR 0.1 |
| 101 | traveling 16244-16454 | traveling 16244-16409 | 1.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.75/0.38 .. 0.61/0.42 | P 0.7, M 0.39, dlogR -0.09 |
| 107 | traveling 16948-17517 | traveling 16963-17068 | 15.5 | weak traveling (steady 22%; P 0.61, M 0.41): kept only the clear part(s) | P 0.61, M 0.41, dlogR -0.03 |
| 120 | milling 19121-19615 | milling 19151-19615 | 1.0 | trimmed to steady milling (M>=0.50 & P<=0.50 held >= 1.0s at edges): start +30 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.21/0.47 .. 0.20/0.53 | P 0.13, M 0.63, dlogR 0.31 |
| 138 | shoaling 21578-21698 | shoaling 21578-21653 | 1.5 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.18/0.29 .. 0.31/0.44 | P 0.19, M 0.36, dlogR -0.01 |
| 150 | shoaling 23496-23826 | shoaling 23511-23781 | 2.0 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +15 fr (+0.5s), end -45 fr (-1.5s); edge P/M before trim 0.47/0.23 .. 0.45/0.17 | P 0.31, M 0.2, dlogR 0.29 |
| 151 | milling 24366-24593 | milling 24471-24530 | 5.6 | weak milling (steady 49%; P 0.13, M 0.48): kept only the clear part(s) / trimmed to steady milling (M>=0.50 & P<=0.50 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.12/0.52 .. 0.15/0.50 | P 0.13, M 0.48, dlogR 0.08 |

### merged (18)

| old_seg | old | new | merged_with_orig | reason | metrics |
|---|---|---|---|---|---|
| 6 | traveling 809-854 | traveling 809-959 | 7;8 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.70/0.05 .. 0.56/0.17 | P 0.73, M 0.07, dlogR 0.04 |
| 11 | traveling 1334-1528 | traveling 1334-1723 | 12;13 | absorbed into a same-label neighbour after an adjacent relabel | P 0.94, M 0.06, dlogR -0.03 |
| 33 | traveling 4496-4690 | traveling 4496-5155 | 34;35;36;37;38;39 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.84/0.28 .. 0.62/0.16 | P 0.78, M 0.21, dlogR 0.08 |
| 37 | traveling 4885-4960 | traveling 4496-5155 | 33;34;35;36;38;39 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.84/0.28 .. 0.62/0.16 | P 0.88, M 0.05, dlogR -0.01 |
| 41 | traveling 5275-5934 | traveling 5395-6234 | 42;43 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +120 fr (+4.0s), end -75 fr (-2.5s); edge P/M before trim 0.51/0.11 .. 0.25/0.11 | P 0.69, M 0.3, dlogR 0.45 |
| 63 | traveling 9590-9815 | traveling 9590-10235 | 64;65;66;67 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.84/0.05 .. 0.63/0.22 | P 0.89, M 0.04, dlogR -0.13 |
| 67 | traveling 10055-10250 | traveling 9590-10235 | 63;64;65;66 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.84/0.05 .. 0.63/0.22 | P 0.77, M 0.11, dlogR -0.14 |
| 78 | traveling 11958-12168 | traveling 11958-12557 | 79;80;81;82 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -165 fr (-5.5s); edge P/M before trim 0.87/0.27 .. 0.62/0.37 | P 0.91, M 0.16, dlogR -0.02 |
| 82 | traveling 12348-12722 | traveling 11958-12557 | 78;79;80;81 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -165 fr (-5.5s); edge P/M before trim 0.87/0.27 .. 0.62/0.37 | P 0.73, M 0.15, dlogR -0.01 |
| 87 | shoaling 13786-13906 | shoaling 13786-14041 | 88;89 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.30/0.28 .. 0.45/0.25 | P 0.12, M 0.28, dlogR 0.11 |
| 95 | traveling 15105-15854 | traveling 15105-15989 | 96;97 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.67/0.16 .. 0.63/0.25 | P 0.77, M 0.1, dlogR -0.28 |
| 111 | traveling 17802-18012 | traveling 17802-18147 | 112;113 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.91/0.15 .. 0.55/0.40 | P 0.89, M 0.12, dlogR -0.02 |
| 118 | traveling 18776-18836 | traveling 18566-18836 | 116;117 | absorbed into a same-label neighbour after an adjacent relabel | P 0.71, M 0.14, dlogR -0.03 |
| 122 | traveling 19780-19930 | traveling 19780-20185 | 123;124 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.72/0.40 .. 0.61/0.03 | P 0.77, M 0.24, dlogR 0.12 |
| 132 | traveling 20949-21189 | traveling 20949-21459 | 133;134;135;136 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.88/0.03 .. 0.59/0.04 | P 0.92, M 0.11, dlogR 0.01 |
| 136 | traveling 21369-21474 | traveling 20949-21459 | 132;133;134;135 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.88/0.03 .. 0.59/0.04 | P 0.68, M 0.09, dlogR -0.03 |
| 144 | traveling 22118-22732 | traveling 22118-23392 | 145;146;147;148 | absorbed into a same-label neighbour after an adjacent relabel | P 0.85, M 0.07, dlogR 0.04 |
| 148 | traveling 22912-23392 | traveling 22118-23392 | 144;145;146;147 | absorbed into a same-label neighbour after an adjacent relabel | P 0.85, M 0.17, dlogR 0.15 |

### new_from_gap (2)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| milling | 10:07.5 | 10:11.5 | 18207-18327 | gap 18162-18521: 4.0s continuous steady milling; P 0.17, M 0.62 |
| compaction | 13:18.5 | 13:20 | 23931-23976 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.09/s (thr 0.08), dlogR -0.16, dur 2.1s, P mean 0.37 min 0.25 (pre 0.45), 0% frames P>=0.65, speed x1.60; inside gap |

### removed (11)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 14 | compaction to traveling 1723-1768 | —  | transition traveling->traveling after neighbour relabel; only 0% steady | P 0.63, M 0.14, dlogR -0.01 |
| 15 | traveling 1768-1978 | —  | weak traveling: steady 20%, no other state >= 60% (milling 0%); P 0.60, M 0.06 -> leave unlabelled | P 0.6, M 0.06, dlogR -0.04 |
| 23 | traveling 2832-2862 | —  | weak traveling: steady 17%, no other state >= 60% (milling 0%); P 0.63, M 0.45 -> leave unlabelled | P 0.63, M 0.45, dlogR -0.01 |
| 29 | milling 3836-4181 | —  | weak milling: steady 26%, no other state >= 60% (shoaling 12%); P 0.17, M 0.46 -> leave unlabelled | P 0.17, M 0.46, dlogR 0.11 |
| 40 | compaction to traveling 5230-5275 | —  | transition traveling->traveling after neighbour relabel; only 0% steady | P 0.56, M 0.15, dlogR -0.04 |
| 103 | milling 16603-16768 | —  | weak milling: steady 25%, no other state >= 60% (shoaling 15%); P 0.18, M 0.47 -> leave unlabelled | P 0.18, M 0.47, dlogR 0.03 |
| 114 | traveling 18521-18551 | —  | weak traveling: steady 0%, no other state >= 60% (milling 0%); P 0.61, M 0.21 -> leave unlabelled | P 0.61, M 0.21, dlogR -0.02 |
| 115 | traveling to compaction 18551-18566 | —  | transition traveling->traveling after neighbour relabel; only 13% steady | P 0.64, M 0.16, dlogR -0.02 |
| 125 | compaction to traveling 20260-20320 | —  | transition traveling->traveling after neighbour relabel; only 0% steady | P 0.63, M 0.04, dlogR -0.04 |
| 126 | traveling 20320-20514 | —  | weak traveling: steady 8%, no other state >= 60% (milling 0%); P 0.58, M 0.08 -> leave unlabelled | P 0.58, M 0.08, dlogR 0.23 |
| 140 | traveling 21923-21953 | —  | weak traveling: steady 53%, no other state >= 60% (milling 0%); P 0.65, M 0.16 -> leave unlabelled | P 0.65, M 0.16, dlogR -0.02 |

### unchanged (74)

Segments: 1, 2, 3, 4, 5, 9, 10, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 30, 31, 32, 46, 47, 48, 49, 50, 51, 52, 53, 54, 56, 57, 58, 59, 60, 61, 62, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 84, 85, 86, 92, 93, 94, 99, 100, 102, 104, 105, 106, 108, 109, 110, 119, 121, 127, 128, 129, 130, 131, 137, 139, 141, 142, 143, 149.

Flagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): 9 (expansion), 16 (traveling to shoaling), 18 (shoaling to milling), 21 (expansion), 22 (expansion to traveling), 24 (traveling to compaction), 28 (traveling to milling), 30 (milling to expansion), 31 (expansion), 47 (expansion), 51 (compaction), 57 (compaction), 61 (expansion), 85 (compaction), 102 (traveling to milling), 104 (milling to compaction), 108 (traveling to expansion), 109 (expansion), 127 (traveling to compaction), 128 (compaction), 130 (expansion), 139 (shoaling to traveling), 141 (traveling to compaction), 142 (compaction).

## 0105 (10_fish): 40 revised segments (from 65); {'unchanged': 26, 'relabel': 19, 'merged': 11, 'boundary_trim': 6, 'removed': 3, 'new_from_gap': 2}

### relabel (19)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 14 | traveling to compaction 7552-7582 | traveling 6833-8496 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.96, M 0.06, dlogR -0.03 |
| 15 | compaction 7582-7642 | traveling 6833-8496 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.23/s (thr 0.24), dlogR -0.26, dur 2.0s, P mean 0.97 min 0.91 (pre 0.96), 100% frames P>=0.65, speed x1.07 | P 0.96, M 0.06, dlogR -0.25 |
| 16 | compaction to traveling 7642-7672 | traveling 6833-8496 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.88, M 0.08, dlogR 0.07 |
| 18 | traveling to compaction 8317-8347 | traveling 6833-8496 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.96, M 0.14, dlogR -0.02 |
| 19 | compaction 8347-8407 | traveling 6833-8496 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.22/s (thr 0.24), dlogR -0.28, dur 2.0s, P mean 0.95 min 0.93 (pre 0.96), 100% frames P>=0.65, speed x1.37 | P 0.95, M 0.06, dlogR -0.28 |
| 20 | compaction to traveling 8407-8437 | traveling 6833-8496 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.96, M 0.04, dlogR -0.02 |
| 37 | traveling to compaction 12812-12842 | traveling 12527-17353 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.87/0.22 .. 0.60/0.29 | P 0.98, M 0.12, dlogR -0.03 |
| 38 | compaction 12842-12902 | traveling 12527-17353 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.34/s (thr 0.24), dlogR -0.43, dur 2.0s, P mean 0.94 min 0.84 (pre 0.98), 100% frames P>=0.65, speed x1.12 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.87/0.22 .. 0.60/0.29 | P 0.94, M 0.08, dlogR -0.42 |
| 39 | compaction to traveling 12902-13007 | traveling 12527-17353 | no state change left after neighbour relabel; 80% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.87/0.22 .. 0.60/0.29 | P 0.77, M 0.4, dlogR 0.27 |
| 46 | traveling to compaction 18222-18252 | traveling 17967-18432 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.93, M 0.08, dlogR -0.04 |
| 47 | compaction 18252-18297 | traveling 17967-18432 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.26/s (thr 0.24), dlogR -0.29, dur 1.5s, P mean 0.91 min 0.88 (pre 0.93), 100% frames P>=0.65, speed x0.85 | P 0.91, M 0.11, dlogR -0.27 |
| 48 | compaction to traveling 18297-18342 | traveling 17967-18432 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.87, M 0.09, dlogR -0.06 |
| 51 | traveling to compaction 20320-20350 | traveling 18626-20410 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end -30 fr (-1.0s); edge P/M before trim 0.57/0.47 .. 0.74/0.28 | P 0.96, M 0.11, dlogR 0.02 |
| 52 | compaction 20350-20440 | traveling 18626-20410 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.27/s (thr 0.24), dlogR -0.52, dur 3.0s, P mean 0.79 min 0.64 (pre 0.95), 94% frames P>=0.65, speed x1.00 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end -30 fr (-1.0s); edge P/M before trim 0.57/0.47 .. 0.74/0.28 | P 0.78, M 0.15, dlogR -0.49 |
| 55 | traveling to compaction 21099-21129 | traveling 20649-21953 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.89, M 0.12, dlogR -0.12 |
| 56 | compaction 21129-21174 | traveling 20649-21953 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.29/s (thr 0.24), dlogR -0.34, dur 1.5s, P mean 0.87 min 0.85 (pre 0.89), 100% frames P>=0.65, speed x1.05 | P 0.87, M 0.08, dlogR -0.3 |
| 57 | compaction to traveling 21174-21219 | traveling 20649-21953 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.9, M 0.17, dlogR 0.2 |
| 60 | expansion 21983-22028 | traveling 21983-22567 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.23/s (thr 0.24), dlogR +0.23, dur 1.5s, P mean 0.77 min 0.63 (pre 0.65), 89% frames P>=0.65, speed x1.97 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.63/0.18 .. 0.79/0.06 | P 0.77, M 0.22, dlogR 0.21 |
| 61 | expansion to traveling 22028-22058 | traveling 21983-22567 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.63/0.18 .. 0.79/0.06 | P 0.91, M 0.12, dlogR 0.01 |

### boundary_trim (6)

| old_seg | old | new | trimmed_s | reason | metrics |
|---|---|---|---|---|---|
| 4 | shoaling 1618-1783 | shoaling 1618-1708 | 2.5 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +0 fr (+0.0s), end -75 fr (-2.5s); edge P/M before trim 0.19/0.11 .. 0.14/0.45 | P 0.24, M 0.29, dlogR 0.63 |
| 8 | traveling 4540-5679 | traveling 4585-5679 | 1.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.63/0.06 .. 0.75/0.13 | P 0.86, M 0.14, dlogR 0.12 |
| 34 | shoaling 12048-12348 | shoaling 12138-12168 | 9.0 | weak shoaling (steady 22%; P 0.47, M 0.25): kept only the clear part(s) / trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +30 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.32/0.14 .. 0.33/0.19 | P 0.47, M 0.25, dlogR 0.46 |
| 44 | traveling 17547-17832 | traveling 17547-17802 | 1.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.80/0.13 .. 0.69/0.31 | P 0.85, M 0.2, dlogR -0.19 |
| 63 | traveling 22837-23676 | traveling 22852-23676 | 0.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.58/0.27 .. 0.72/0.29 | P 0.86, M 0.16, dlogR 0.21 |
| 64 | traveling 23826-24578 | traveling 23841-24560 | 1.1 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end -18 fr (-0.6s); edge P/M before trim 0.56/0.07 .. 0.41/0.09 | P 0.93, M 0.12, dlogR 0.15 |

### merged (11)

| old_seg | old | new | merged_with_orig | reason | metrics |
|---|---|---|---|---|---|
| 13 | traveling 6833-7552 | traveling 6833-8496 | 14;15;16;17;18;19;20;21 | absorbed into a same-label neighbour after an adjacent relabel | P 0.89, M 0.12, dlogR 0.5 |
| 17 | traveling 7672-8317 | traveling 6833-8496 | 13;14;15;16;18;19;20;21 | absorbed into a same-label neighbour after an adjacent relabel | P 0.83, M 0.11, dlogR 0.1 |
| 21 | traveling 8437-8496 | traveling 6833-8496 | 13;14;15;16;17;18;19;20 | absorbed into a same-label neighbour after an adjacent relabel | P 0.91, M 0.07, dlogR -0.02 |
| 36 | traveling 12527-12812 | traveling 12527-17353 | 37;38;39;40 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.87/0.22 .. 0.60/0.29 | P 0.95, M 0.1, dlogR -0.2 |
| 40 | traveling 13007-17368 | traveling 12527-17353 | 36;37;38;39 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.87/0.22 .. 0.60/0.29 | P 0.86, M 0.14, dlogR -0.46 |
| 45 | traveling 17967-18222 | traveling 17967-18432 | 46;47;48;49 | absorbed into a same-label neighbour after an adjacent relabel | P 0.95, M 0.09, dlogR -0.21 |
| 49 | traveling 18342-18432 | traveling 17967-18432 | 45;46;47;48 | absorbed into a same-label neighbour after an adjacent relabel | P 0.82, M 0.14, dlogR -0.15 |
| 50 | traveling 18611-20320 | traveling 18626-20410 | 51;52 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end -30 fr (-1.0s); edge P/M before trim 0.57/0.47 .. 0.74/0.28 | P 0.87, M 0.18, dlogR 0.16 |
| 54 | traveling 20649-21099 | traveling 20649-21953 | 55;56;57;58 | absorbed into a same-label neighbour after an adjacent relabel | P 0.93, M 0.09, dlogR 0.63 |
| 58 | traveling 21219-21953 | traveling 20649-21953 | 54;55;56;57 | absorbed into a same-label neighbour after an adjacent relabel | P 0.83, M 0.21, dlogR 0.15 |
| 62 | traveling 22058-22612 | traveling 21983-22567 | 60;61 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.63/0.18 .. 0.79/0.06 | P 0.9, M 0.12, dlogR -0.73 |

### new_from_gap (2)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| compaction | 03:09.5 | 03:11.5 | 5679-5739 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.32/s (thr 0.24), dlogR -0.44, dur 2.4s, P mean 0.52 min 0.31 (pre 0.74), 18% frames P>=0.65, speed x1.35; inside gap |
| expansion | 10:18.5 | 10:20.5 | 18536-18596 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.39/s (thr 0.24), dlogR +0.56, dur 2.6s, P mean 0.46 min 0.38 (pre 0.42), 0% frames P>=0.65, speed x1.40; inside gap |

### removed (3)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 24 | milling 9336-9441 | —  | weak milling: steady 23%, no other state >= 60% (traveling 0%); P 0.47, M 0.46 -> leave unlabelled | P 0.47, M 0.46, dlogR 0.18 |
| 53 | compaction to traveling 20440-20649 | —  | transition traveling->traveling after neighbour relabel; only 52% steady | P 0.67, M 0.21, dlogR 0.06 |
| 59 | traveling to expansion 21953-21983 | —  | transition traveling->traveling after neighbour relabel; only 50% steady | P 0.66, M 0.15, dlogR 0.09 |

### unchanged (26)

Segments: 0, 1, 2, 3, 5, 6, 7, 9, 10, 11, 12, 22, 23, 25, 26, 27, 28, 29, 30, 31, 32, 33, 35, 41, 42, 43.

Flagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): 23 (traveling to milling), 25 (milling to traveling), 35 (shoaling to traveling), 42 (expansion).

## 0107 (70_fish): 53 revised segments (from 72); {'unchanged': 35, 'relabel': 18, 'merged': 7, 'removed': 5, 'boundary_trim': 5, 'new_from_gap': 5, 'split': 2}

### relabel (18)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 3 | traveling to compaction 1558-1618 | traveling 959-2023 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +180 fr (+6.0s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.30 .. 0.65/0.37 | P 0.81, M 0.14, dlogR -0.06 |
| 4 | compaction 1618-1723 | traveling 959-2023 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.07/s (thr 0.05), dlogR -0.19, dur 3.5s, P mean 0.73 min 0.65 (pre 0.80), 99% frames P>=0.65, speed x0.88 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +180 fr (+6.0s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.30 .. 0.65/0.37 | P 0.73, M 0.25, dlogR -0.18 |
| 5 | compaction to traveling 1723-1768 | traveling 959-2023 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +180 fr (+6.0s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.30 .. 0.65/0.37 | P 0.78, M 0.3, dlogR 0.01 |
| 40 | traveling to compaction 16783-16828 | traveling / traveling 16603-16738 / 16783-17113 | no state change left after neighbour relabel; 100% frames steady traveling / weak traveling (steady 59%; P 0.65, M 0.17): kept only the clear part(s) | P 0.71, M 0.27, dlogR -0.03 |
| 41 | compaction 16828-16948 | traveling / traveling 16603-16738 / 16783-17113 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.08/s (thr 0.05), dlogR -0.20, dur 4.0s, P mean 0.81 min 0.76 (pre 0.73), 100% frames P>=0.65, speed x1.39 / weak traveling (steady 59%; P 0.65, M 0.17): kept only the clear part(s) | P 0.81, M 0.24, dlogR -0.2 |
| 42 | compaction to traveling 16948-16993 | traveling / traveling 16603-16738 / 16783-17113 | no state change left after neighbour relabel; 100% frames steady traveling / weak traveling (steady 59%; P 0.65, M 0.17): kept only the clear part(s) | P 0.81, M 0.13, dlogR -0.01 |
| 45 | expansion 17473-17622 | traveling 17502-18117 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.11/s (thr 0.05), dlogR +0.37, dur 5.0s, P mean 0.70 min 0.61 (pre 0.61), 81% frames P>=0.65, speed x1.75 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +29 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.62/0.31 .. 0.91/0.07 | P 0.7, M 0.35, dlogR 0.36 |
| 46 | expansion to compaction 17622-17682 | traveling 17502-18117 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +29 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.62/0.31 .. 0.91/0.07 | P 0.83, M 0.2, dlogR 0.02 |
| 47 | compaction 17682-17892 | traveling 17502-18117 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.07/s (thr 0.05), dlogR -0.33, dur 7.0s, P mean 0.87 min 0.83 (pre 0.86), 100% frames P>=0.65, speed x1.24 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +29 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.62/0.31 .. 0.91/0.07 | P 0.87, M 0.2, dlogR -0.32 |
| 48 | compaction to traveling 17892-17952 | traveling 17502-18117 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +29 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.62/0.31 .. 0.91/0.07 | P 0.86, M 0.23, dlogR -0.06 |
| 57 | traveling to expansion 20170-20200 | traveling 19630-20754 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.76/0.26 .. 0.53/0.21 | P 0.84, M 0.19, dlogR 0.0 |
| 58 | expansion 20200-20305 | traveling 19630-20754 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.07/s (thr 0.05), dlogR +0.17, dur 3.5s, P mean 0.86 min 0.81 (pre 0.84), 100% frames P>=0.65, speed x1.57 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.76/0.26 .. 0.53/0.21 | P 0.86, M 0.19, dlogR 0.16 |
| 59 | expansion to traveling 20305-20350 | traveling 19630-20754 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.76/0.26 .. 0.53/0.21 | P 0.88, M 0.16, dlogR -0.02 |
| 64 | traveling to compaction 22552-22597 | traveling 22088-22702 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.88, M 0.04, dlogR -0.04 |
| 65 | compaction 22597-22702 | traveling 22088-22702 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.07/s (thr 0.05), dlogR -0.12, dur 3.5s, P mean 0.75 min 0.69 (pre 0.87), 100% frames P>=0.65, speed x0.85 | P 0.75, M 0.13, dlogR -0.12 |
| 68 | traveling to compaction 23661-23706 | traveling 23167-23886 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +390 fr (+13.0s), end +0 fr (+0.0s); edge P/M before trim 0.56/0.38 .. 0.65/0.08 | P 0.86, M 0.08, dlogR -0.03 |
| 69 | compaction 23706-23886 | traveling 23167-23886 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.07/s (thr 0.05), dlogR -0.25, dur 6.0s, P mean 0.80 min 0.64 (pre 0.86), 95% frames P>=0.65, speed x1.12 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +390 fr (+13.0s), end +0 fr (+0.0s); edge P/M before trim 0.56/0.38 .. 0.65/0.08 | P 0.8, M 0.03, dlogR -0.25 |
| 70 | compaction to shoaling 23886-23946 | traveling to shoaling 23886-23946 | transition renamed because neighbour was relabelled | P 0.4, M 0.09, dlogR 0.07 |

### boundary_trim (5)

| old_seg | old | new | trimmed_s | reason | metrics |
|---|---|---|---|---|---|
| 11 | traveling 6414-7268 | traveling 6489-7268 | 2.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +75 fr (+2.5s), end +0 fr (+0.0s); edge P/M before trim 0.57/0.05 .. 0.89/0.10 | P 0.72, M 0.2, dlogR -0.0 |
| 15 | traveling 7642-8212 | traveling 7747-8062 | 8.5 | weak traveling (steady 59%; P 0.66, M 0.13): kept only the clear part(s) | P 0.66, M 0.13, dlogR 0.1 |
| 26 | milling 11359-11823 | milling 11493-11823 | 4.5 | trimmed to steady milling (M>=0.50 & P<=0.50 held >= 1.0s at edges): start +134 fr (+4.5s), end +0 fr (+0.0s); edge P/M before trim 0.20/0.43 .. 0.40/0.59 | P 0.23, M 0.52, dlogR 0.14 |
| 28 | traveling 12228-12827 | traveling 12228-12797 | 1.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.76/0.17 .. 0.65/0.20 | P 0.81, M 0.07, dlogR 0.0 |
| 33 | milling 15165-15884 | milling 15165-15824 | 2.0 | trimmed to steady milling (M>=0.50 & P<=0.50 held >= 1.0s at edges): start +0 fr (+0.0s), end -60 fr (-2.0s); edge P/M before trim 0.24/0.56 .. 0.30/0.45 | P 0.22, M 0.57, dlogR -0.03 |

### split (2)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 39 | traveling 16573-16783 | traveling / traveling 16603-16738 / 16783-17113 | weak traveling (steady 59%; P 0.65, M 0.17): kept only the clear part(s) | P 0.67, M 0.1, dlogR 0.25 |
| 43 | traveling 16993-17413 | traveling / traveling 16603-16738 / 16783-17113 | weak traveling (steady 59%; P 0.65, M 0.17): kept only the clear part(s) | P 0.56, M 0.17, dlogR -0.16 |

### merged (7)

| old_seg | old | new | merged_with_orig | reason | metrics |
|---|---|---|---|---|---|
| 2 | traveling 779-1558 | traveling 959-2023 | 3;4;5;6 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +180 fr (+6.0s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.30 .. 0.65/0.37 | P 0.77, M 0.22, dlogR 0.18 |
| 6 | traveling 1768-2023 | traveling 959-2023 | 2;3;4;5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +180 fr (+6.0s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.30 .. 0.65/0.37 | P 0.72, M 0.32, dlogR 0.06 |
| 49 | traveling 17952-18117 | traveling 17502-18117 | 45;46;47;48 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +29 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.62/0.31 .. 0.91/0.07 | P 0.89, M 0.07, dlogR 0.04 |
| 56 | traveling 19630-20170 | traveling 19630-20754 | 57;58;59;60 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.76/0.26 .. 0.53/0.21 | P 0.85, M 0.16, dlogR 0.04 |
| 60 | traveling 20350-20799 | traveling 19630-20754 | 56;57;58;59 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.76/0.26 .. 0.53/0.21 | P 0.84, M 0.09, dlogR 0.13 |
| 63 | traveling 22088-22552 | traveling 22088-22702 | 64;65 | absorbed into a same-label neighbour after an adjacent relabel | P 0.81, M 0.23, dlogR -0.03 |
| 67 | traveling 22777-23661 | traveling 23167-23886 | 68;69 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +390 fr (+13.0s), end +0 fr (+0.0s); edge P/M before trim 0.56/0.38 .. 0.65/0.08 | P 0.68, M 0.25, dlogR 0.1 |

### new_from_gap (5)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| shoaling | 05:18.5 | 05:22.5 | 9545-9665 | gap 9545-9920: 4.0s continuous steady shoaling; P 0.30, M 0.05 |
| shoaling | 07:31 | 07:34.5 | 13516-13621 | gap 13442-13726: 3.5s continuous steady shoaling; P 0.29, M 0.33 |
| milling | 07:51.5 | 07:56.5 | 14131-14281 | gap 13966-14476: 5.0s continuous steady milling; P 0.27, M 0.59 |
| shoaling | 08:08.5 | 08:14 | 14640-14805 | gap 14640-15165: 5.5s continuous steady shoaling; P 0.30, M 0.32 |
| shoaling | 13:37 | 13:40 | 24485-24575 | gap 24231-24578: 3.0s continuous steady shoaling; P 0.36, M 0.05 |

### removed (5)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 10 | traveling 5769-5979 | —  | weak traveling: steady 7%, no other state >= 60% (milling 0%); P 0.59, M 0.12 -> leave unlabelled | P 0.59, M 0.12, dlogR -0.15 |
| 31 | traveling 13726-13966 | —  | weak traveling: steady 0%, no other state >= 60% (milling 0%); P 0.54, M 0.23 -> leave unlabelled | P 0.54, M 0.23, dlogR -0.05 |
| 35 | traveling 16244-16349 | —  | weak traveling: steady 18%, no other state >= 60% (milling 0%); P 0.63, M 0.10 -> leave unlabelled | P 0.63, M 0.1, dlogR -0.04 |
| 44 | traveling to expansion 17413-17473 | —  | transition traveling->traveling after neighbour relabel; only 0% steady | P 0.57, M 0.24, dlogR 0.09 |
| 66 | compaction to traveling 22702-22777 | —  | transition traveling->traveling after neighbour relabel; only 40% steady | P 0.63, M 0.3, dlogR 0.03 |

### unchanged (35)

Segments: 0, 1, 7, 8, 9, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 27, 29, 30, 32, 34, 36, 37, 38, 50, 51, 52, 53, 54, 55, 61, 62, 71.

Flagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): 1 (milling to traveling), 9 (milling to traveling), 16 (traveling to shoaling), 18 (compaction), 22 (expansion), 34 (milling to traveling), 36 (traveling to compaction).

## 0115 (30_fish): 69 revised segments (from 114); {'unchanged': 45, 'relabel': 39, 'merged': 17, 'boundary_trim': 8, 'removed': 4, 'new_event_in_segment': 2, 'new_from_gap': 2, 'split': 1}

### relabel (39)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 13 | compaction 5080-5185 | traveling 5080-5185 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.20/s (thr 0.13), dlogR -0.46, dur 3.5s, P mean 0.81 min 0.72 (pre 0.75), 100% frames P>=0.65, speed x1.46 | P 0.81, M 0.07, dlogR -0.45 |
| 14 | compaction to shoaling 5185-5245 | traveling to shoaling 5185-5245 | transition renamed because neighbour was relabelled / transition kept as is (rule 3) but its 'to' state segment is not adjacent any more (trimmed/removed neighbour or original gap) | P 0.58, M 0.13, dlogR -0.05 |
| 18 | traveling to compaction 5485-5514 | traveling 5410-8137 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.71, M 0.17, dlogR -0.08 |
| 19 | compaction 5514-5604 | traveling 5410-8137 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.18/s (thr 0.13), dlogR -0.45, dur 3.0s, P mean 0.68 min 0.63 (pre 0.71), 82% frames P>=0.65, speed x1.52 | P 0.68, M 0.1, dlogR -0.43 |
| 20 | compaction to traveling 5604-5649 | traveling 5410-8137 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.76, M 0.21, dlogR 0.05 |
| 22 | traveling to compaction 7073-7088 | traveling 5410-8137 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.8, M 0.17, dlogR -0.01 |
| 23 | compaction 7088-7178 | traveling 5410-8137 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.14/s (thr 0.13), dlogR -0.25, dur 3.0s, P mean 0.70 min 0.64 (pre 0.82), 92% frames P>=0.65, speed x1.08 | P 0.7, M 0.12, dlogR -0.24 |
| 24 | compaction to traveling 7178-7223 | traveling 5410-8137 | no state change left after neighbour relabel; 96% frames steady traveling | P 0.71, M 0.04, dlogR 0.08 |
| 26 | traveling to expansion 7403-7418 | traveling 5410-8137 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.87, M 0.32, dlogR 0.03 |
| 27 | expansion 7418-7478 | traveling 5410-8137 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.22/s (thr 0.13), dlogR +0.34, dur 2.0s, P mean 0.93 min 0.89 (pre 0.85), 100% frames P>=0.65, speed x2.55 | P 0.94, M 0.11, dlogR 0.32 |
| 28 | expansion to traveling 7478-7492 | traveling 5410-8137 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.97, M 0.08, dlogR -0.01 |
| 30 | traveling to compaction 7657-7672 | traveling 5410-8137 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.95, M 0.07, dlogR -0.01 |
| 31 | compaction 7672-7747 | traveling 5410-8137 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.17/s (thr 0.13), dlogR -0.29, dur 2.5s, P mean 0.93 min 0.84 (pre 0.96), 100% frames P>=0.65, speed x1.07 | P 0.93, M 0.06, dlogR -0.28 |
| 32 | compaction to traveling 7747-7777 | traveling 5410-8137 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.79, M 0.22, dlogR -0.07 |
| 45 | shoaling 10460-10609 | compaction 10504-10594 (remnants < 2 s left unlabelled) | split around new compaction 10504-10594 | P 0.19, M 0.14, dlogR -0.56 |
| 53 | traveling to expansion 14176-14191 | traveling 13681-14490 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.9, M 0.04, dlogR 0.02 |
| 54 | expansion 14191-14251 | traveling 13681-14490 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.14/s (thr 0.13), dlogR +0.20, dur 2.0s, P mean 0.93 min 0.88 (pre 0.87), 100% frames P>=0.65, speed x2.37 | P 0.93, M 0.04, dlogR 0.18 |
| 55 | expansion to traveling 14251-14266 | traveling 13681-14490 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.97, M 0.03, dlogR -0.02 |
| 69 | traveling to compaction 18357-18372 | traveling 18012-18536 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.84, M 0.33, dlogR -0.03 |
| 70 | compaction 18372-18447 | traveling 18012-18536 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.13/s (thr 0.13), dlogR -0.25, dur 2.5s, P mean 0.85 min 0.83 (pre 0.84), 100% frames P>=0.65, speed x1.10 | P 0.85, M 0.27, dlogR -0.24 |
| 71 | compaction to traveling 18447-18477 | traveling 18012-18536 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.87, M 0.1, dlogR -0.01 |
| 77 | traveling to compaction 19211-19241 | traveling 18851-20080 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.68/0.09 .. 0.58/0.38 | P 0.92, M 0.09, dlogR -0.06 |
| 78 | compaction 19241-19316 | traveling 18851-20080 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.14/s (thr 0.13), dlogR -0.22, dur 2.5s, P mean 0.90 min 0.88 (pre 0.92), 100% frames P>=0.65, speed x1.00 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.68/0.09 .. 0.58/0.38 | P 0.9, M 0.08, dlogR -0.21 |
| 79 | compaction to traveling 19316-19346 | traveling 18851-20080 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.68/0.09 .. 0.58/0.38 | P 0.91, M 0.09, dlogR 0.01 |
| 81 | traveling to expansion 19825-19840 | traveling 18851-20080 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.68/0.09 .. 0.58/0.38 | P 0.77, M 0.15, dlogR 0.03 |
| 82 | expansion 19840-19930 | traveling 18851-20080 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.12/s (thr 0.13), dlogR +0.25, dur 3.0s, P mean 0.75 min 0.71 (pre 0.76), 100% frames P>=0.65, speed x1.64 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.68/0.09 .. 0.58/0.38 | P 0.75, M 0.15, dlogR 0.24 |
| 83 | expansion to traveling 19930-19960 | traveling 18851-20080 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.68/0.09 .. 0.58/0.38 | P 0.82, M 0.21, dlogR 0.0 |
| 89 | traveling to compaction 20305-20320 | traveling 20230-20470 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.96, M 0.2, dlogR -0.02 |
| 90 | compaction 20320-20470 | traveling 20230-20470 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.17/s (thr 0.13), dlogR -0.47, dur 5.0s, P mean 0.94 min 0.89 (pre 0.95), 100% frames P>=0.65, speed x0.96 | P 0.94, M 0.11, dlogR -0.47 |
| 91 | compaction to shoaling 20470-20589 | traveling to shoaling 20470-20589 | transition renamed because neighbour was relabelled / transition kept as is (rule 3) but its 'to' state segment is not adjacent any more (trimmed/removed neighbour or original gap) | P 0.74, M 0.22, dlogR -0.16 |
| 97 | traveling to compaction 20964-20994 | traveling 20904-21264 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.97, M 0.06, dlogR -0.03 |
| 98 | compaction 20994-21159 | traveling 20904-21264 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.11/s (thr 0.13), dlogR -0.45, dur 5.5s, P mean 0.95 min 0.93 (pre 0.97), 100% frames P>=0.65, speed x0.82 | P 0.95, M 0.07, dlogR -0.44 |
| 99 | compaction to traveling 21159-21189 | traveling 20904-21264 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.93, M 0.03, dlogR -0.04 |
| 102 | milling 21429-21653 | expansion 21488-21608 (remnants < 2 s left unlabelled) | split around new expansion 21488-21608 | P 0.3, M 0.51, dlogR 0.5 |
| 105 | traveling to compaction 22927-22942 | traveling 21803-23676 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.97, M 0.04, dlogR -0.02 |
| 106 | compaction 22942-23032 | traveling 21803-23676 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.13), dlogR -0.25, dur 3.0s, P mean 0.94 min 0.89 (pre 0.97), 100% frames P>=0.65, speed x0.90 | P 0.94, M 0.06, dlogR -0.24 |
| 107 | compaction to traveling 23032-23062 | traveling 21803-23676 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.91, M 0.11, dlogR -0.0 |
| 109 | traveling to compaction 23556-23571 | traveling 21803-23676 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.92, M 0.09, dlogR -0.02 |
| 110 | compaction 23571-23676 | traveling 21803-23676 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.14/s (thr 0.13), dlogR -0.37, dur 3.5s, P mean 0.83 min 0.72 (pre 0.90), 100% frames P>=0.65, speed x1.97 | P 0.83, M 0.2, dlogR -0.36 |

### boundary_trim (8)

| old_seg | old | new | trimmed_s | reason | metrics |
|---|---|---|---|---|---|
| 5 | shoaling 3072-3192 | shoaling 3102-3192 | 1.0 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +30 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.43/0.27 .. 0.25/0.22 | P 0.21, M 0.3, dlogR 0.1 |
| 7 | traveling 3297-3686 | traveling 3357-3686 | 2.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +60 fr (+2.0s), end +0 fr (+0.0s); edge P/M before trim 0.71/0.24 .. 0.69/0.16 | P 0.73, M 0.17, dlogR 0.22 |
| 48 | traveling 13187-13576 | traveling 13277-13576 | 3.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +90 fr (+3.0s), end +0 fr (+0.0s); edge P/M before trim 0.59/0.29 .. 0.96/0.02 | P 0.8, M 0.09, dlogR -0.09 |
| 59 | traveling 15405-15659 | traveling 15569-15629 | 6.5 | weak traveling (steady 33%; P 0.63, M 0.19): kept only the clear part(s) | P 0.63, M 0.19, dlogR 0.05 |
| 60 | traveling 15824-16633 | traveling 15839-16633 | 0.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.65/0.34 .. 0.82/0.07 | P 0.8, M 0.18, dlogR -0.37 |
| 66 | shoaling 17682-17847 | shoaling 17712-17787 | 3.0 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +30 fr (+1.0s), end -60 fr (-2.0s); edge P/M before trim 0.36/0.28 .. 0.27/0.34 | P 0.34, M 0.31, dlogR 0.12 |
| 111 | milling 23976-24381 | milling 24111-24381 | 4.5 | trimmed to steady milling (M>=0.50 & P<=0.50 held >= 1.0s at edges): start +135 fr (+4.5s), end +0 fr (+0.0s); edge P/M before trim 0.69/0.49 .. 0.49/0.78 | P 0.47, M 0.6, dlogR 0.14 |
| 113 | traveling 24500-24593 | traveling 24515-24575 | 1.1 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end -18 fr (-0.6s); edge P/M before trim 0.67/0.36 .. 0.34/0.06 | P 0.68, M 0.13, dlogR -0.12 |

### split (1)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 58 | shoaling 14595-14955 | shoaling / shoaling 14715-14775 / 14835-14895 | weak shoaling (steady 53%; P 0.40, M 0.17): kept only the clear part(s) | P 0.4, M 0.17, dlogR 0.15 |

### merged (17)

| old_seg | old | new | merged_with_orig | reason | metrics |
|---|---|---|---|---|---|
| 17 | traveling 5410-5485 | traveling 5410-8137 | 18;19;20;21;22;23;24;25;26;27;28;29;30;31;32;33 | absorbed into a same-label neighbour after an adjacent relabel | P 0.73, M 0.16, dlogR 0.24 |
| 21 | traveling 5649-7073 | traveling 5410-8137 | 17;18;19;20;22;23;24;25;26;27;28;29;30;31;32;33 | absorbed into a same-label neighbour after an adjacent relabel | P 0.84, M 0.14, dlogR 0.11 |
| 25 | traveling 7223-7403 | traveling 5410-8137 | 17;18;19;20;21;22;23;24;26;27;28;29;30;31;32;33 | absorbed into a same-label neighbour after an adjacent relabel | P 0.85, M 0.2, dlogR -0.11 |
| 29 | traveling 7492-7657 | traveling 5410-8137 | 17;18;19;20;21;22;23;24;25;26;27;28;30;31;32;33 | absorbed into a same-label neighbour after an adjacent relabel | P 0.97, M 0.07, dlogR 0.19 |
| 33 | traveling 7777-8137 | traveling 5410-8137 | 17;18;19;20;21;22;23;24;25;26;27;28;29;30;31;32 | absorbed into a same-label neighbour after an adjacent relabel | P 0.84, M 0.11, dlogR 0.2 |
| 52 | traveling 13681-14176 | traveling 13681-14490 | 53;54;55;56 | absorbed into a same-label neighbour after an adjacent relabel | P 0.83, M 0.09, dlogR -0.06 |
| 56 | traveling 14266-14490 | traveling 13681-14490 | 52;53;54;55 | absorbed into a same-label neighbour after an adjacent relabel | P 0.88, M 0.06, dlogR -0.33 |
| 68 | traveling 18012-18357 | traveling 18012-18536 | 69;70;71;72 | absorbed into a same-label neighbour after an adjacent relabel | P 0.9, M 0.16, dlogR -0.09 |
| 72 | traveling 18477-18536 | traveling 18012-18536 | 68;69;70;71 | absorbed into a same-label neighbour after an adjacent relabel | P 0.86, M 0.13, dlogR 0.05 |
| 76 | traveling 18851-19211 | traveling 18851-20080 | 77;78;79;80;81;82;83;84 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.68/0.09 .. 0.58/0.38 | P 0.81, M 0.28, dlogR 0.39 |
| 80 | traveling 19346-19825 | traveling 18851-20080 | 76;77;78;79;81;82;83;84 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.68/0.09 .. 0.58/0.38 | P 0.8, M 0.24, dlogR -0.04 |
| 84 | traveling 19960-20095 | traveling 18851-20080 | 76;77;78;79;80;81;82;83 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.68/0.09 .. 0.58/0.38 | P 0.78, M 0.27, dlogR -0.22 |
| 88 | traveling 20230-20305 | traveling 20230-20470 | 89;90 | absorbed into a same-label neighbour after an adjacent relabel | P 0.95, M 0.13, dlogR -0.14 |
| 96 | traveling 20904-20964 | traveling 20904-21264 | 97;98;99;100 | absorbed into a same-label neighbour after an adjacent relabel | P 0.96, M 0.06, dlogR 0.0 |
| 100 | traveling 21189-21264 | traveling 20904-21264 | 96;97;98;99 | absorbed into a same-label neighbour after an adjacent relabel | P 0.88, M 0.04, dlogR -0.1 |
| 104 | traveling 21803-22927 | traveling 21803-23676 | 105;106;107;108;109;110 | absorbed into a same-label neighbour after an adjacent relabel | P 0.84, M 0.18, dlogR -0.14 |
| 108 | traveling 23062-23556 | traveling 21803-23676 | 104;105;106;107;109;110 | absorbed into a same-label neighbour after an adjacent relabel | P 0.81, M 0.13, dlogR 0.34 |

### new_from_gap (2)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| expansion | 07:06 | 07:07.5 | 12767-12812 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.15/s (thr 0.13), dlogR +0.23, dur 1.9s, P mean 0.49 min 0.37 (pre 0.35), 0% frames P>=0.65, speed x1.49; inside gap |
| traveling | 07:08 | 07:11 | 12827-12917 | gap 12557-13187: 3.0s continuous steady traveling; P 0.72, M 0.40 |

### new_event_in_segment (2)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| compaction | 05:50.5 | 05:53.5 | 10504-10594 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.26/s (thr 0.13), dlogR -0.58, dur 3.8s, P mean 0.17 min 0.05 (pre 0.20), 0% frames P>=0.65, speed x1.48; carved from shoaling |
| expansion | 11:57 | 12:01 | 21488-21608 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.15/s (thr 0.13), dlogR +0.41, dur 4.4s, P mean 0.30 min 0.23 (pre 0.33), 0% frames P>=0.65, speed x1.53; carved from milling |

### removed (4)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 15 | shoaling 5245-5335 | —  | weak shoaling: steady 31%, no other state >= 60% (traveling 0%); P 0.43, M 0.29 -> leave unlabelled | P 0.43, M 0.29, dlogR 0.02 |
| 62 | shoaling 16933-17098 | —  | weak shoaling: steady 38%, no clear run >= 2.0s after grid snap; P 0.36, M 0.18 | P 0.36, M 0.18, dlogR -0.14 |
| 74 | shoaling 18581-18731 | —  | weak shoaling: steady 20%, no other state >= 60% (traveling 0%); P 0.46, M 0.09 -> leave unlabelled | P 0.46, M 0.09, dlogR -0.34 |
| 92 | shoaling 20589-20694 | —  | weak shoaling: steady 31%, no other state >= 60% (milling 15%); P 0.24, M 0.43 -> leave unlabelled | P 0.24, M 0.43, dlogR 0.13 |

### unchanged (45)

Segments: 0, 1, 2, 3, 4, 6, 8, 9, 10, 11, 12, 16, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47, 49, 50, 51, 57, 61, 63, 64, 65, 67, 73, 75, 85, 86, 87, 93, 94, 95, 101, 103, 112.

Flagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): 8 (compaction), 16 (shoaling to traveling), 44 (traveling to shoaling), 46 (shoaling to traveling), 61 (traveling to shoaling), 63 (shoaling to traveling), 73 (traveling to shoaling), 75 (shoaling to traveling), 86 (expansion), 93 (shoaling to expansion), 101 (traveling to milling), 103 (milling to traveling).

## 0120 (30_fish): 75 revised segments (from 147); {'relabel': 64, 'unchanged': 43, 'merged': 26, 'boundary_trim': 9, 'removed': 5, 'new_from_gap': 2, 'new_event_in_segment': 1}

### relabel (64)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 1 | expansion to compaction 195-225 | expansion to traveling 195-225 | transition renamed because neighbour was relabelled | P 0.93, M 0.09, dlogR -0.03 |
| 2 | compaction 225-315 | traveling 225-779 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.12), dlogR -0.22, dur 3.0s, P mean 0.95 min 0.94 (pre 0.93), 100% frames P>=0.65, speed x1.32 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.95/0.04 .. 0.60/0.21 | P 0.95, M 0.09, dlogR -0.21 |
| 3 | compaction to traveling 315-345 | traveling 225-779 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.95/0.04 .. 0.60/0.21 | P 0.93, M 0.17, dlogR -0.04 |
| 5 | traveling to expansion 435-450 | traveling 225-779 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.95/0.04 .. 0.60/0.21 | P 0.92, M 0.11, dlogR 0.02 |
| 6 | expansion 450-524 | traveling 225-779 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.19/s (thr 0.12), dlogR +0.33, dur 2.5s, P mean 0.94 min 0.94 (pre 0.89), 100% frames P>=0.65, speed x1.21 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.95/0.04 .. 0.60/0.21 | P 0.94, M 0.11, dlogR 0.31 |
| 7 | expansion to traveling 524-554 | traveling 225-779 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.95/0.04 .. 0.60/0.21 | P 0.95, M 0.04, dlogR -0.02 |
| 10 | traveling to compaction 1004-1019 | traveling 959-1469 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.64/0.51 .. 0.86/0.27 | P 0.95, M 0.04, dlogR -0.01 |
| 11 | compaction 1019-1124 | traveling 959-1469 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.14/s (thr 0.12), dlogR -0.34, dur 3.5s, P mean 0.93 min 0.83 (pre 0.93), 100% frames P>=0.65, speed x1.28 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.64/0.51 .. 0.86/0.27 | P 0.93, M 0.1, dlogR -0.33 |
| 12 | compaction to expansion 1124-1154 | traveling 959-1469 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.64/0.51 .. 0.86/0.27 | P 0.9, M 0.21, dlogR -0.01 |
| 13 | expansion 1154-1199 | traveling 959-1469 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.20/s (thr 0.12), dlogR +0.21, dur 1.5s, P mean 0.94 min 0.92 (pre 0.90), 100% frames P>=0.65, speed x1.47 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.64/0.51 .. 0.86/0.27 | P 0.94, M 0.1, dlogR 0.2 |
| 14 | expansion to compaction 1199-1229 | traveling 959-1469 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.64/0.51 .. 0.86/0.27 | P 0.94, M 0.15, dlogR -0.01 |
| 15 | compaction 1229-1274 | traveling 959-1469 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.12/s (thr 0.12), dlogR -0.11, dur 1.5s, P mean 0.95 min 0.92 (pre 0.94), 100% frames P>=0.65, speed x1.29 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.64/0.51 .. 0.86/0.27 | P 0.95, M 0.06, dlogR -0.11 |
| 16 | compaction to traveling 1274-1304 | traveling 959-1469 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.64/0.51 .. 0.86/0.27 | P 0.96, M 0.06, dlogR 0.01 |
| 24 | traveling to compaction 2128-2158 | traveling 2098-2877 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.88, M 0.04, dlogR -0.04 |
| 25 | compaction 2158-2263 | traveling 2098-2877 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.12), dlogR -0.27, dur 3.5s, P mean 0.92 min 0.89 (pre 0.88), 100% frames P>=0.65, speed x1.47 | P 0.92, M 0.1, dlogR -0.26 |
| 26 | compaction to traveling 2263-2308 | traveling 2098-2877 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.86, M 0.05, dlogR -0.09 |
| 30 | compaction to expansion 2967-3057 | compaction to traveling 2967-3057 | transition renamed because neighbour was relabelled | P 0.57, M 0.4, dlogR -0.01 |
| 31 | expansion 3057-3147 | traveling 3057-3671 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.12/s (thr 0.12), dlogR +0.25, dur 3.0s, P mean 0.82 min 0.68 (pre 0.68), 100% frames P>=0.65, speed x1.55 | P 0.82, M 0.19, dlogR 0.24 |
| 32 | expansion to traveling 3147-3177 | traveling 3057-3671 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.9, M 0.12, dlogR 0.04 |
| 34 | traveling to compaction 3506-3521 | traveling 3057-3671 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.88, M 0.14, dlogR -0.01 |
| 35 | compaction 3521-3581 | traveling 3057-3671 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.17/s (thr 0.12), dlogR -0.25, dur 2.0s, P mean 0.91 min 0.86 (pre 0.87), 100% frames P>=0.65, speed x1.17 | P 0.91, M 0.22, dlogR -0.23 |
| 36 | compaction to traveling 3581-3611 | traveling 3057-3671 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.87, M 0.2, dlogR -0.01 |
| 44 | traveling to compaction 4421-4436 | traveling 4196-5365 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.97, M 0.06, dlogR -0.02 |
| 45 | compaction 4436-4600 | traveling 4196-5365 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.11/s (thr 0.12), dlogR -0.39, dur 5.5s, P mean 0.95 min 0.90 (pre 0.96), 100% frames P>=0.65, speed x0.94 | P 0.95, M 0.15, dlogR -0.38 |
| 46 | compaction to traveling 4600-4660 | traveling 4196-5365 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.91, M 0.17, dlogR -0.04 |
| 48 | traveling to compaction 5215-5230 | traveling 4196-5365 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.87, M 0.05, dlogR -0.01 |
| 49 | compaction 5230-5290 | traveling 4196-5365 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.12), dlogR -0.12, dur 2.0s, P mean 0.85 min 0.78 (pre 0.85), 100% frames P>=0.65, speed x0.96 | P 0.85, M 0.05, dlogR -0.12 |
| 50 | compaction to traveling 5290-5320 | traveling 4196-5365 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.84, M 0.06, dlogR -0.01 |
| 68 | traveling to compaction 12857-12887 | traveling 12438-13037 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.85, M 0.23, dlogR -0.04 |
| 69 | compaction 12887-13037 | traveling 12438-13037 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.12/s (thr 0.12), dlogR -0.29, dur 5.0s, P mean 0.81 min 0.75 (pre 0.85), 100% frames P>=0.65, speed x1.22 | P 0.8, M 0.19, dlogR -0.29 |
| 70 | compaction to milling 13037-13157 | traveling to milling 13037-13157 | transition renamed because neighbour was relabelled | P 0.54, M 0.38, dlogR -0.19 |
| 75 | expansion 14251-14326 | traveling 14251-14505 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.16/s (thr 0.12), dlogR +0.21, dur 2.5s, P mean 0.73 min 0.65 (pre 0.61), 100% frames P>=0.65, speed x1.58 | P 0.73, M 0.04, dlogR 0.21 |
| 76 | expansion to traveling 14326-14356 | traveling 14251-14505 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.89, M 0.05, dlogR -0.03 |
| 80 | shoaling to expansion 14835-14955 | shoaling to traveling 14835-14955 | transition renamed because neighbour was relabelled | P 0.56, M 0.15, dlogR 0.18 |
| 81 | expansion 14955-15030 | traveling 14955-16154 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.14/s (thr 0.12), dlogR +0.25, dur 2.5s, P mean 0.86 min 0.73 (pre 0.74), 100% frames P>=0.65, speed x3.41 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.74/0.16 .. 0.54/0.30 | P 0.86, M 0.11, dlogR 0.24 |
| 82 | expansion to traveling 15030-15060 | traveling 14955-16154 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.74/0.16 .. 0.54/0.30 | P 0.97, M 0.03, dlogR -0.03 |
| 84 | traveling to compaction 16094-16109 | traveling 14955-16154 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.74/0.16 .. 0.54/0.30 | P 0.86, M 0.13, dlogR -0.01 |
| 85 | compaction 16109-16184 | traveling 14955-16154 | strict exp/comp: -> traveling (not rapid; 75% frames steady traveling); peak dlogR/dt 0.11/s (thr 0.12), dlogR -0.22, dur 2.5s, P mean 0.70 min 0.53 (pre 0.86), 75% frames P>=0.65, speed x0.77 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.74/0.16 .. 0.54/0.30 | P 0.7, M 0.23, dlogR -0.21 |
| 86 | compaction to shoaling 16184-16214 | traveling to shoaling 16184-16214 | transition renamed because neighbour was relabelled / transition kept as is (rule 3) but its 'to' state segment is not adjacent any more (trimmed/removed neighbour or original gap) | P 0.49, M 0.36, dlogR -0.02 |
| 98 | traveling to compaction 18132-18162 | traveling 18072-18282 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.72/0.09 .. 0.63/0.39 | P 0.73, M 0.19, dlogR -0.05 |
| 99 | compaction 18162-18297 | traveling 18072-18282 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.16/s (thr 0.12), dlogR -0.46, dur 4.5s, P mean 0.73 min 0.63 (pre 0.73), 95% frames P>=0.65, speed x1.28 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.72/0.09 .. 0.63/0.39 | P 0.73, M 0.26, dlogR -0.45 |
| 100 | compaction to shoaling 18297-18372 | traveling to shoaling 18297-18372 | transition renamed because neighbour was relabelled / transition kept as is (rule 3) but its 'to' state segment is not adjacent any more (trimmed/removed neighbour or original gap) | P 0.59, M 0.38, dlogR -0.01 |
| 104 | traveling to expansion 18671-18686 | traveling 18641-19331 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.82, M 0.42, dlogR 0.01 |
| 105 | expansion 18686-18761 | traveling 18641-19331 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.12/s (thr 0.12), dlogR +0.20, dur 2.5s, P mean 0.86 min 0.81 (pre 0.82), 100% frames P>=0.65, speed x1.68 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.86, M 0.42, dlogR 0.19 |
| 106 | expansion to compaction 18761-18821 | traveling 18641-19331 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.9, M 0.35, dlogR -0.02 |
| 107 | compaction 18821-18896 | traveling 18641-19331 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.07/s (thr 0.12), dlogR -0.13, dur 2.5s, P mean 0.81 min 0.74 (pre 0.88), 100% frames P>=0.65, speed x0.99 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.81, M 0.42, dlogR -0.13 |
| 108 | compaction to traveling 18896-18926 | traveling 18641-19331 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.74, M 0.45, dlogR -0.03 |
| 110 | traveling to expansion 18956-18971 | traveling 18641-19331 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.76, M 0.43, dlogR 0.01 |
| 111 | expansion 18971-19061 | traveling 18641-19331 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.14/s (thr 0.12), dlogR +0.31, dur 3.0s, P mean 0.83 min 0.71 (pre 0.74), 100% frames P>=0.65, speed x2.23 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.83, M 0.37, dlogR 0.3 |
| 112 | expansion to traveling 19061-19091 | traveling 18641-19331 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.91, M 0.22, dlogR 0.04 |
| 114 | traveling to compaction 19211-19226 | traveling 18641-19331 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.9, M 0.23, dlogR -0.01 |
| 115 | compaction 19226-19376 | traveling 18641-19331 | strict exp/comp: -> traveling (not rapid; 74% frames steady traveling); peak dlogR/dt 0.11/s (thr 0.12), dlogR -0.28, dur 5.0s, P mean 0.76 min 0.51 (pre 0.90), 74% frames P>=0.65, speed x0.86 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.76, M 0.27, dlogR -0.27 |
| 118 | traveling to compaction 20095-20110 | traveling 19525-20365 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.63/0.43 .. 0.75/0.26 | P 0.92, M 0.12, dlogR -0.02 |
| 119 | compaction 20110-20200 | traveling 19525-20365 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.15/s (thr 0.12), dlogR -0.29, dur 3.0s, P mean 0.87 min 0.84 (pre 0.93), 100% frames P>=0.65, speed x1.14 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.63/0.43 .. 0.75/0.26 | P 0.87, M 0.11, dlogR -0.28 |
| 120 | compaction to traveling 20200-20230 | traveling 19525-20365 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.63/0.43 .. 0.75/0.26 | P 0.87, M 0.16, dlogR 0.02 |
| 126 | traveling to expansion 21249-21264 | traveling 20649-21578 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.91, M 0.2, dlogR -0.0 |
| 127 | expansion 21264-21339 | traveling 20649-21578 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.08/s (thr 0.12), dlogR +0.13, dur 2.5s, P mean 0.92 min 0.90 (pre 0.89), 100% frames P>=0.65, speed x1.70 | P 0.92, M 0.18, dlogR 0.12 |
| 128 | expansion to traveling 21339-21369 | traveling 20649-21578 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.93, M 0.21, dlogR 0.01 |
| 133 | traveling to expansion 22058-22073 | traveling 21908-22253 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.69/0.39 .. 0.52/0.11 | P 0.68, M 0.28, dlogR 0.02 |
| 134 | expansion 22073-22163 | traveling 21908-22253 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.09/s (thr 0.12), dlogR +0.18, dur 3.0s, P mean 0.72 min 0.69 (pre 0.66), 100% frames P>=0.65, speed x1.31 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.69/0.39 .. 0.52/0.11 | P 0.72, M 0.29, dlogR 0.17 |
| 135 | expansion to traveling 22163-22193 | traveling 21908-22253 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.69/0.39 .. 0.52/0.11 | P 0.78, M 0.26, dlogR 0.02 |
| 141 | traveling to compaction 23032-23047 | traveling 22478-24471 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.92, M 0.04, dlogR -0.0 |
| 142 | compaction 23047-23137 | traveling 22478-24471 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.13/s (thr 0.12), dlogR -0.26, dur 3.0s, P mean 0.86 min 0.79 (pre 0.94), 100% frames P>=0.65, speed x0.91 | P 0.86, M 0.08, dlogR -0.25 |
| 143 | compaction to traveling 23137-23167 | traveling 22478-24471 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.8, M 0.22, dlogR -0.0 |

### boundary_trim (9)

| old_seg | old | new | trimmed_s | reason | metrics |
|---|---|---|---|---|---|
| 19 | shoaling 1528-1948 | shoaling 1543-1948 | 0.5 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.44/0.31 .. 0.39/0.20 | P 0.32, M 0.19, dlogR -0.07 |
| 39 | milling 3761-4001 | milling 3761-3911 | 3.0 | trimmed to steady milling (M>=0.50 & P<=0.50 held >= 1.0s at edges): start +0 fr (+0.0s), end -90 fr (-3.0s); edge P/M before trim 0.43/0.51 .. 0.51/0.55 | P 0.41, M 0.6, dlogR -0.16 |
| 66 | milling 11299-12048 | milling 11299-11928 | 4.0 | split around new compaction 11928-12003 | P 0.17, M 0.62, dlogR 0.31 |
| 73 | traveling 13666-14236 | traveling 13666-14101 | 4.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -135 fr (-4.5s); edge P/M before trim 0.89/0.09 .. 0.63/0.15 | P 0.83, M 0.13, dlogR -0.35 |
| 79 | shoaling 14670-14835 | shoaling 14790-14835 | 4.0 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +120 fr (+4.0s), end +0 fr (+0.0s); edge P/M before trim 0.40/0.33 .. 0.30/0.29 | P 0.35, M 0.32, dlogR -0.04 |
| 89 | traveling 16454-16603 | traveling 16484-16603 | 1.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +30 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.60/0.08 .. 0.70/0.12 | P 0.68, M 0.04, dlogR 0.19 |
| 93 | shoaling 16843-17068 | shoaling 16903-17068 | 2.0 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +60 fr (+2.0s), end +0 fr (+0.0s); edge P/M before trim 0.46/0.20 .. 0.24/0.03 | P 0.33, M 0.09, dlogR 0.47 |
| 94 | traveling 17263-17383 | traveling 17293-17383 | 1.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +30 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.58/0.05 .. 0.75/0.39 | P 0.72, M 0.14, dlogR -0.14 |
| 96 | milling 17443-17637 | milling 17443-17607 | 1.0 | trimmed to steady milling (M>=0.50 & P<=0.50 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.47/0.65 .. 0.46/0.36 | P 0.31, M 0.6, dlogR 0.14 |

### merged (26)

| old_seg | old | new | merged_with_orig | reason | metrics |
|---|---|---|---|---|---|
| 4 | traveling 345-435 | traveling 225-779 | 2;3;5;6;7;8 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.95/0.04 .. 0.60/0.21 | P 0.89, M 0.17, dlogR -0.21 |
| 8 | traveling 554-824 | traveling 225-779 | 2;3;4;5;6;7 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.95/0.04 .. 0.60/0.21 | P 0.78, M 0.11, dlogR -0.09 |
| 9 | traveling 944-1004 | traveling 959-1469 | 10;11;12;13;14;15;16;17 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.64/0.51 .. 0.86/0.27 | P 0.82, M 0.27, dlogR 0.17 |
| 17 | traveling 1304-1469 | traveling 959-1469 | 9;10;11;12;13;14;15;16 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.64/0.51 .. 0.86/0.27 | P 0.93, M 0.13, dlogR -0.04 |
| 23 | traveling 2098-2128 | traveling 2098-2877 | 24;25;26;27 | absorbed into a same-label neighbour after an adjacent relabel | P 0.85, M 0.07, dlogR 0.0 |
| 27 | traveling 2308-2877 | traveling 2098-2877 | 23;24;25;26 | absorbed into a same-label neighbour after an adjacent relabel | P 0.88, M 0.16, dlogR 0.2 |
| 33 | traveling 3177-3506 | traveling 3057-3671 | 31;32;34;35;36;37 | absorbed into a same-label neighbour after an adjacent relabel | P 0.87, M 0.06, dlogR -0.01 |
| 37 | traveling 3611-3671 | traveling 3057-3671 | 31;32;33;34;35;36 | absorbed into a same-label neighbour after an adjacent relabel | P 0.82, M 0.28, dlogR 0.04 |
| 43 | traveling 4196-4421 | traveling 4196-5365 | 44;45;46;47;48;49;50;51 | absorbed into a same-label neighbour after an adjacent relabel | P 0.93, M 0.11, dlogR 0.04 |
| 47 | traveling 4660-5215 | traveling 4196-5365 | 43;44;45;46;48;49;50;51 | absorbed into a same-label neighbour after an adjacent relabel | P 0.86, M 0.22, dlogR 0.32 |
| 51 | traveling 5320-5365 | traveling 4196-5365 | 43;44;45;46;47;48;49;50 | absorbed into a same-label neighbour after an adjacent relabel | P 0.81, M 0.07, dlogR 0.01 |
| 67 | traveling 12438-12857 | traveling 12438-13037 | 68;69 | absorbed into a same-label neighbour after an adjacent relabel | P 0.73, M 0.38, dlogR 0.16 |
| 77 | traveling 14356-14505 | traveling 14251-14505 | 75;76 | absorbed into a same-label neighbour after an adjacent relabel | P 0.84, M 0.13, dlogR -0.09 |
| 83 | traveling 15060-16094 | traveling 14955-16154 | 81;82;84;85 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.74/0.16 .. 0.54/0.30 | P 0.85, M 0.18, dlogR -0.06 |
| 97 | traveling 18072-18132 | traveling 18072-18282 | 98;99 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -15 fr (-0.5s); edge P/M before trim 0.72/0.09 .. 0.63/0.39 | P 0.77, M 0.13, dlogR -0.04 |
| 103 | traveling 18641-18671 | traveling 18641-19331 | 104;105;106;107;108;109;110;111;112;113;114;115 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.81, M 0.41, dlogR 0.0 |
| 109 | traveling 18926-18956 | traveling 18641-19331 | 103;104;105;106;107;108;110;111;112;113;114;115 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.74, M 0.36, dlogR -0.01 |
| 113 | traveling 19091-19211 | traveling 18641-19331 | 103;104;105;106;107;108;109;110;111;112;114;115 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.79/0.40 .. 0.52/0.29 | P 0.91, M 0.22, dlogR 0.06 |
| 117 | traveling 19480-20095 | traveling 19525-20365 | 118;119;120;121 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.63/0.43 .. 0.75/0.26 | P 0.83, M 0.31, dlogR -0.03 |
| 121 | traveling 20230-20365 | traveling 19525-20365 | 117;118;119;120 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.63/0.43 .. 0.75/0.26 | P 0.81, M 0.13, dlogR -0.13 |
| 125 | traveling 20649-21249 | traveling 20649-21578 | 126;127;128;129 | absorbed into a same-label neighbour after an adjacent relabel | P 0.79, M 0.19, dlogR 0.34 |
| 129 | traveling 21369-21578 | traveling 20649-21578 | 125;126;127;128 | absorbed into a same-label neighbour after an adjacent relabel | P 0.86, M 0.18, dlogR -0.31 |
| 132 | traveling 21908-22058 | traveling 21908-22253 | 133;134;135;136 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.69/0.39 .. 0.52/0.11 | P 0.68, M 0.35, dlogR -0.0 |
| 136 | traveling 22193-22298 | traveling 21908-22253 | 132;133;134;135 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.69/0.39 .. 0.52/0.11 | P 0.67, M 0.15, dlogR -0.09 |
| 140 | traveling 22478-23032 | traveling 22478-24471 | 141;142;143;144 | absorbed into a same-label neighbour after an adjacent relabel | P 0.83, M 0.16, dlogR -0.05 |
| 144 | traveling 23167-24471 | traveling 22478-24471 | 140;141;142;143 | absorbed into a same-label neighbour after an adjacent relabel | P 0.86, M 0.23, dlogR 0.38 |

### new_from_gap (2)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| shoaling | 06:44.5 | 06:49 | 12123-12258 | gap 12048-12438: 4.5s continuous steady shoaling; P 0.23, M 0.29 |
| compaction | 06:49 | 06:51 | 12258-12318 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.15/s (thr 0.12), dlogR -0.33, dur 2.8s, P mean 0.50 min 0.28 (pre 0.29), 0% frames P>=0.65, speed x1.39; inside gap |

### new_event_in_segment (1)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| compaction | 06:38 | 06:40.5 | 11928-12003 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.15/s (thr 0.12), dlogR -0.35, dur 3.2s, P mean 0.17 min 0.09 (pre 0.09), 0% frames P>=0.65, speed x1.49; carved from milling |

### removed (5)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 74 | traveling to expansion 14236-14251 | —  | transition traveling->traveling after neighbour relabel; only 13% steady | P 0.64, M 0.09, dlogR 0.02 |
| 87 | shoaling 16214-16349 | —  | weak shoaling: steady 19%, no other state >= 60% (milling 8%); P 0.25, M 0.44 -> leave unlabelled | P 0.25, M 0.44, dlogR 0.17 |
| 101 | shoaling 18372-18536 | —  | weak shoaling: steady 19%, no other state >= 60% (traveling 0%); P 0.45, M 0.18 -> leave unlabelled | P 0.45, M 0.18, dlogR 0.31 |
| 116 | compaction to traveling 19376-19480 | —  | transition traveling->traveling after neighbour relabel; only 0% steady | P 0.54, M 0.45, dlogR 0.15 |
| 123 | shoaling 20440-20544 | —  | weak shoaling: steady 13%, no other state >= 60% (traveling 0%); P 0.46, M 0.19 -> leave unlabelled | P 0.46, M 0.19, dlogR 0.1 |

### unchanged (43)

Segments: 0, 18, 20, 21, 22, 28, 29, 38, 40, 41, 42, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 71, 72, 78, 88, 90, 91, 92, 95, 102, 122, 124, 130, 131, 137, 138, 139, 145, 146.

Flagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): 0 (expansion), 88 (shoaling to traveling), 102 (shoaling to traveling), 122 (traveling to shoaling), 124 (shoaling to traveling), 131 (compaction), 138 (compaction).

## 0124 (70_fish): 51 revised segments (from 64); {'unchanged': 39, 'relabel': 9, 'removed': 6, 'merged': 5, 'boundary_trim': 4, 'new_from_gap': 2, 'split': 1}

### relabel (9)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 14 | milling to compaction 10265-10549 | milling to traveling 10265-10549 | transition renamed because neighbour was relabelled | P 0.41, M 0.49, dlogR 0.01 |
| 15 | compaction 10549-10654 | traveling 10564-11269 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.05/s (thr 0.05), dlogR -0.13, dur 3.5s, P mean 0.69 min 0.62 (pre 0.57), 93% frames P>=0.65, speed x1.37 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.62/0.24 .. 0.72/0.15 | P 0.69, M 0.24, dlogR -0.13 |
| 16 | compaction to traveling 10654-10699 | traveling 10564-11269 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.62/0.24 .. 0.72/0.15 | P 0.75, M 0.22, dlogR -0.03 |
| 24 | traveling to compaction 13067-13112 | traveling 12318-13561 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -225 fr (-7.5s); edge P/M before trim 0.62/0.35 .. 0.57/0.09 | P 0.71, M 0.13, dlogR -0.03 |
| 25 | compaction 13112-13232 | traveling 12318-13561 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.05/s (thr 0.05), dlogR -0.13, dur 4.0s, P mean 0.69 min 0.65 (pre 0.71), 100% frames P>=0.65, speed x1.19 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -225 fr (-7.5s); edge P/M before trim 0.62/0.35 .. 0.57/0.09 | P 0.68, M 0.15, dlogR -0.12 |
| 26 | compaction to traveling 13232-13277 | traveling 12318-13561 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -225 fr (-7.5s); edge P/M before trim 0.62/0.35 .. 0.57/0.09 | P 0.72, M 0.17, dlogR -0.0 |
| 53 | traveling to compaction 19690-19720 | traveling 19615-20125 | no state change left after neighbour relabel; 100% frames steady traveling / weak traveling (steady 54%; P 0.66, M 0.08): kept only the clear part(s) | P 0.79, M 0.04, dlogR -0.01 |
| 54 | compaction 19720-19855 | traveling 19615-20125 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.05), dlogR -0.29, dur 4.5s, P mean 0.83 min 0.80 (pre 0.79), 100% frames P>=0.65, speed x1.15 / weak traveling (steady 54%; P 0.66, M 0.08): kept only the clear part(s) | P 0.83, M 0.09, dlogR -0.29 |
| 55 | compaction to traveling 19855-19900 | traveling 19615-20125 | no state change left after neighbour relabel; 100% frames steady traveling / weak traveling (steady 54%; P 0.66, M 0.08): kept only the clear part(s) | P 0.76, M 0.15, dlogR 0.01 |

### boundary_trim (4)

| old_seg | old | new | trimmed_s | reason | metrics |
|---|---|---|---|---|---|
| 31 | traveling 15090-15719 | traveling 15390-15719 | 10.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +300 fr (+10.0s), end +0 fr (+0.0s); edge P/M before trim 0.64/0.14 .. 0.70/0.06 | P 0.71, M 0.27, dlogR -0.13 |
| 43 | milling 17982-18162 | milling 18027-18162 | 1.5 | trimmed to steady milling (M>=0.50 & P<=0.50 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.13/0.52 .. 0.20/0.58 | P 0.13, M 0.57, dlogR 0.16 |
| 51 | traveling 18821-19241 | traveling 18836-19196 | 2.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end -45 fr (-1.5s); edge P/M before trim 0.63/0.09 .. 0.59/0.17 | P 0.7, M 0.13, dlogR 0.07 |
| 61 | traveling 22657-23227 | traveling 22657-23182 | 1.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -45 fr (-1.5s); edge P/M before trim 0.67/0.29 .. 0.61/0.54 | P 0.8, M 0.27, dlogR -0.4 |

### split (1)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 39 | traveling 16783-17697 | traveling / traveling 17323-17458 / 17517-17682 | weak traveling (steady 42%; P 0.64, M 0.29): kept only the clear part(s) / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +60 fr (+2.0s), end +0 fr (+0.0s); edge P/M before trim 0.66/0.32 .. 0.67/0.37 | P 0.64, M 0.29, dlogR 0.05 |

### merged (5)

| old_seg | old | new | merged_with_orig | reason | metrics |
|---|---|---|---|---|---|
| 17 | traveling 10699-11269 | traveling 10564-11269 | 15;16 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.62/0.24 .. 0.72/0.15 | P 0.87, M 0.11, dlogR 0.07 |
| 23 | traveling 12318-13067 | traveling 12318-13561 | 24;25;26;27 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -225 fr (-7.5s); edge P/M before trim 0.62/0.35 .. 0.57/0.09 | P 0.81, M 0.13, dlogR -0.06 |
| 27 | traveling 13277-13786 | traveling 12318-13561 | 23;24;25;26 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -225 fr (-7.5s); edge P/M before trim 0.62/0.35 .. 0.57/0.09 | P 0.67, M 0.1, dlogR 0.21 |
| 52 | traveling 19600-19690 | traveling 19615-20125 | 53;54;55;56 | weak traveling (steady 54%; P 0.66, M 0.08): kept only the clear part(s) | P 0.78, M 0.04, dlogR 0.05 |
| 56 | traveling 19900-20634 | traveling 19615-20125 | 52;53;54;55 | weak traveling (steady 54%; P 0.66, M 0.08): kept only the clear part(s) | P 0.6, M 0.08, dlogR 0.12 |

### new_from_gap (2)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| shoaling | 00:19 | 00:22 | 569-659 | gap 0-809: 3.0s continuous steady shoaling; P 0.28, M 0.35 |
| shoaling | 13:27 | 13:30 | 24186-24276 | gap 24081-24351: 3.0s continuous steady shoaling; P 0.34, M 0.35 |

### removed (6)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 3 | traveling 6953-7163 | —  | weak traveling: steady 15%, no other state >= 60% (milling 0%); P 0.62, M 0.29 -> leave unlabelled | P 0.62, M 0.29, dlogR 0.06 |
| 7 | traveling 7522-7897 | —  | weak traveling: steady 8%, no other state >= 60% (milling 0%); P 0.57, M 0.19 -> leave unlabelled | P 0.57, M 0.19, dlogR 0.09 |
| 35 | traveling 16004-16094 | —  | weak traveling: steady 0%, no other state >= 60% (milling 0%); P 0.51, M 0.05 -> leave unlabelled | P 0.51, M 0.05, dlogR -0.03 |
| 47 | traveling 18432-18462 | —  | weak traveling: steady 0%, no other state >= 60% (milling 0%); P 0.57, M 0.18 -> leave unlabelled | P 0.57, M 0.18, dlogR -0.02 |
| 62 | traveling 23736-24081 | —  | weak traveling: steady 0%, no other state >= 60% (milling 0%); P 0.57, M 0.38 -> leave unlabelled | P 0.57, M 0.38, dlogR -0.21 |
| 63 | traveling 24351-24533 | —  | weak traveling: steady 36%, no clear run >= 2.0s after grid snap; P 0.62, M 0.36 | P 0.62, M 0.36, dlogR 0.01 |

### unchanged (39)

Segments: 0, 1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 18, 19, 20, 21, 22, 28, 29, 30, 32, 33, 34, 36, 37, 38, 40, 41, 42, 44, 45, 46, 48, 49, 50, 57, 58, 59, 60.

Flagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): 2 (milling to traveling), 4 (traveling to compaction), 5 (compaction), 6 (compaction to traveling), 8 (traveling to expansion), 9 (expansion), 28 (traveling to shoaling), 30 (shoaling to traveling), 33 (compaction), 34 (compaction to traveling), 36 (traveling to shoaling), 38 (shoaling to traveling), 41 (compaction), 46 (expansion to traveling), 48 (traveling to compaction), 49 (compaction), 57 (traveling to compaction).

## 0126 (10_fish): 24 revised segments (from 61); {'relabel': 29, 'unchanged': 17, 'merged': 12, 'boundary_trim': 2, 'removed': 1, 'new_from_gap': 1, 'new_event_in_segment': 1}

### relabel (29)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 2 | traveling to compaction 1484-1498 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.94, M 0.07, dlogR -0.04 |
| 3 | compaction 1498-1588 | traveling 1004-13292 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.22/s (thr 0.22), dlogR -0.51, dur 3.0s, P mean 0.81 min 0.71 (pre 0.95), 100% frames P>=0.65, speed x1.10 | P 0.81, M 0.08, dlogR -0.49 |
| 4 | compaction to traveling 1588-1618 | traveling 1004-13292 | no state change left after neighbour relabel; 83% frames steady traveling | P 0.75, M 0.1, dlogR -0.04 |
| 6 | traveling to expansion 3252-3267 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.96, M 0.08, dlogR 0.01 |
| 7 | expansion 3267-3327 | traveling 1004-13292 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.41/s (thr 0.22), dlogR +0.46, dur 2.0s, P mean 0.94 min 0.92 (pre 0.96), 100% frames P>=0.65, speed x1.20 | P 0.94, M 0.16, dlogR 0.44 |
| 8 | expansion to traveling 3327-3357 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.95, M 0.1, dlogR -0.01 |
| 10 | traveling to compaction 4436-4451 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.85, M 0.1, dlogR -0.03 |
| 11 | compaction 4451-4525 | traveling 1004-13292 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.26/s (thr 0.22), dlogR -0.33, dur 2.5s, P mean 0.81 min 0.73 (pre 0.86), 100% frames P>=0.65, speed x1.14 | P 0.81, M 0.16, dlogR -0.32 |
| 12 | compaction to traveling 4525-4555 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.86, M 0.2, dlogR 0.01 |
| 14 | traveling to compaction 5544-5559 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.92, M 0.06, dlogR 0.02 |
| 15 | compaction 5559-5634 | traveling 1004-13292 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.29/s (thr 0.22), dlogR -0.35, dur 2.5s, P mean 0.93 min 0.90 (pre 0.89), 100% frames P>=0.65, speed x0.81 | P 0.93, M 0.04, dlogR -0.36 |
| 16 | compaction to traveling 5634-5664 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.95, M 0.06, dlogR 0.04 |
| 18 | traveling to compaction 10579-10594 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.93, M 0.05, dlogR -0.02 |
| 19 | compaction 10594-10654 | traveling 1004-13292 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.15/s (thr 0.22), dlogR -0.19, dur 2.0s, P mean 0.94 min 0.91 (pre 0.91), 100% frames P>=0.65, speed x0.93 | P 0.94, M 0.05, dlogR -0.18 |
| 20 | compaction to traveling 10654-10684 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.9, M 0.15, dlogR 0.02 |
| 22 | traveling to compaction 11958-11973 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.98, M 0.15, dlogR -0.04 |
| 23 | compaction 11973-12048 | traveling 1004-13292 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.17/s (thr 0.22), dlogR -0.32, dur 2.5s, P mean 0.90 min 0.83 (pre 0.97), 100% frames P>=0.65, speed x0.80 | P 0.9, M 0.11, dlogR -0.32 |
| 24 | compaction to traveling 12048-12078 | traveling 1004-13292 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.88, M 0.22, dlogR -0.07 |
| 43 | compaction 17622-17682 | traveling 17622-20604 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.28/s (thr 0.22), dlogR -0.42, dur 2.0s, P mean 0.88 min 0.73 (pre 0.65), 100% frames P>=0.65, speed x1.67 | P 0.88, M 0.11, dlogR -0.38 |
| 44 | compaction to traveling 17682-17712 | traveling 17622-20604 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.91, M 0.04, dlogR -0.02 |
| 46 | traveling to compaction 17802-17817 | traveling 17622-20604 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.76, M 0.18, dlogR -0.02 |
| 47 | compaction 17817-17862 | traveling 17622-20604 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.34/s (thr 0.22), dlogR -0.32, dur 1.5s, P mean 0.93 min 0.85 (pre 0.73), 100% frames P>=0.65, speed x1.69 | P 0.94, M 0.05, dlogR -0.29 |
| 48 | compaction to traveling 17862-17892 | traveling 17622-20604 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.92, M 0.06, dlogR -0.04 |
| 50 | traveling to expansion 19945-19960 | traveling 17622-20604 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.93, M 0.06, dlogR 0.06 |
| 51 | expansion 19960-20020 | traveling 17622-20604 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.28/s (thr 0.22), dlogR +0.40, dur 2.0s, P mean 0.91 min 0.88 (pre 0.93), 100% frames P>=0.65, speed x1.74 | P 0.91, M 0.15, dlogR 0.38 |
| 52 | expansion to traveling 20020-20050 | traveling 17622-20604 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.93, M 0.17, dlogR -0.03 |
| 57 | traveling to expansion 24231-24246 | traveling 23287-24620 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -18 fr (-0.6s); edge P/M before trim 0.68/0.12 .. 0.38/0.16 | P 0.91, M 0.28, dlogR 0.05 |
| 58 | expansion 24246-24336 | traveling 23287-24620 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.34/s (thr 0.22), dlogR +0.50, dur 3.0s, P mean 0.93 min 0.90 (pre 0.91), 100% frames P>=0.65, speed x1.90 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -18 fr (-0.6s); edge P/M before trim 0.68/0.12 .. 0.38/0.16 | P 0.93, M 0.21, dlogR 0.48 |
| 59 | expansion to traveling 24336-24351 | traveling 23287-24620 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -18 fr (-0.6s); edge P/M before trim 0.68/0.12 .. 0.38/0.16 | P 0.96, M 0.15, dlogR -0.01 |

### boundary_trim (2)

| old_seg | old | new | trimmed_s | reason | metrics |
|---|---|---|---|---|---|
| 42 | traveling 14595-17368 | traveling 14595-17338 | 1.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.85/0.05 .. 0.70/0.60 | P 0.88, M 0.16, dlogR 0.05 |
| 54 | traveling 20724-21024 | traveling 20754-21024 | 1.0 | split around new expansion 20619-20739 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +15 fr (+0.5s), end +0 fr (+0.0s); edge P/M before trim 0.65/0.03 .. 0.77/0.44 | P 0.86, M 0.41, dlogR -0.59 |

### merged (12)

| old_seg | old | new | merged_with_orig | reason | metrics |
|---|---|---|---|---|---|
| 1 | traveling 1004-1484 | traveling 1004-13292 | 2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23;24;25 | absorbed into a same-label neighbour after an adjacent relabel | P 0.94, M 0.06, dlogR 0.44 |
| 5 | traveling 1618-3252 | traveling 1004-13292 | 1;2;3;4;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23;24;25 | absorbed into a same-label neighbour after an adjacent relabel | P 0.89, M 0.15, dlogR 0.18 |
| 9 | traveling 3357-4436 | traveling 1004-13292 | 1;2;3;4;5;6;7;8;10;11;12;13;14;15;16;17;18;19;20;21;22;23;24;25 | absorbed into a same-label neighbour after an adjacent relabel | P 0.94, M 0.12, dlogR 0.18 |
| 13 | traveling 4555-5544 | traveling 1004-13292 | 1;2;3;4;5;6;7;8;9;10;11;12;14;15;16;17;18;19;20;21;22;23;24;25 | absorbed into a same-label neighbour after an adjacent relabel | P 0.9, M 0.12, dlogR 0.39 |
| 17 | traveling 5664-10579 | traveling 1004-13292 | 1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;18;19;20;21;22;23;24;25 | absorbed into a same-label neighbour after an adjacent relabel | P 0.91, M 0.12, dlogR 0.3 |
| 21 | traveling 10684-11958 | traveling 1004-13292 | 1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;22;23;24;25 | absorbed into a same-label neighbour after an adjacent relabel | P 0.92, M 0.12, dlogR 0.35 |
| 25 | traveling 12078-13292 | traveling 1004-13292 | 1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23;24 | absorbed into a same-label neighbour after an adjacent relabel | P 0.84, M 0.22, dlogR 0.12 |
| 45 | traveling 17712-17802 | traveling 17622-20604 | 43;44;46;47;48;49;50;51;52;53 | absorbed into a same-label neighbour after an adjacent relabel | P 0.85, M 0.08, dlogR 0.26 |
| 49 | traveling 17892-19945 | traveling 17622-20604 | 43;44;45;46;47;48;50;51;52;53 | absorbed into a same-label neighbour after an adjacent relabel | P 0.89, M 0.17, dlogR 0.05 |
| 53 | traveling 20050-20604 | traveling 17622-20604 | 43;44;45;46;47;48;49;50;51;52 | absorbed into a same-label neighbour after an adjacent relabel | P 0.91, M 0.11, dlogR -0.1 |
| 56 | traveling 23287-24231 | traveling 23287-24620 | 57;58;59;60 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -18 fr (-0.6s); edge P/M before trim 0.68/0.12 .. 0.38/0.16 | P 0.9, M 0.14, dlogR 0.21 |
| 60 | traveling 24351-24638 | traveling 23287-24620 | 56;57;58;59 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -18 fr (-0.6s); edge P/M before trim 0.68/0.12 .. 0.38/0.16 | P 0.91, M 0.13, dlogR -0.33 |

### new_from_gap (1)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| compaction | 07:41 | 07:44 | 13816-13906 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.43/s (thr 0.22), dlogR -0.97, dur 3.3s, P mean 0.61 min 0.36 (pre 0.83), 45% frames P>=0.65, speed x1.68; inside gap |

### new_event_in_segment (1)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| expansion | 11:28 | 11:32 | 20619-20739 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.31/s (thr 0.22), dlogR +0.75, dur 4.7s, P mean 0.58 min 0.33 (pre 0.67), 31% frames P>=0.65, speed x2.40; carved from traveling |

### removed (1)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 27 | shoaling 13352-13546 | —  | weak shoaling: steady 27%, no other state >= 60% (traveling 5%); P 0.46, M 0.16 -> leave unlabelled | P 0.46, M 0.16, dlogR 0.27 |

### unchanged (17)

Segments: 0, 26, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 55.

Flagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): 26 (traveling to shoaling), 28 (shoaling to traveling).

## 0200 (150_fish): 61 revised segments (from 107); {'relabel': 51, 'unchanged': 31, 'merged': 16, 'new_from_gap': 5, 'boundary_trim': 5, 'removed': 4, 'new_event_in_segment': 1}

### relabel (51)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 1 | traveling to compaction 360-420 | traveling 150-524 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +30 fr (+1.0s), end -30 fr (-1.0s); edge P/M before trim 0.59/0.11 .. 0.63/0.11 | P 0.85, M 0.03, dlogR -0.1 |
| 2 | compaction 420-554 | traveling 150-524 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.16/s (thr 0.09), dlogR -0.56, dur 4.5s, P mean 0.71 min 0.62 (pre 0.83), 85% frames P>=0.65, speed x0.85 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +30 fr (+1.0s), end -30 fr (-1.0s); edge P/M before trim 0.59/0.11 .. 0.63/0.11 | P 0.71, M 0.04, dlogR -0.55 |
| 4 | expansion 659-764 | traveling 659-1349 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.09/s (thr 0.09), dlogR +0.25, dur 3.5s, P mean 0.74 min 0.68 (pre 0.66), 100% frames P>=0.65, speed x1.81 | P 0.74, M 0.37, dlogR 0.24 |
| 5 | expansion to compaction 764-794 | traveling 659-1349 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.84, M 0.25, dlogR 0.04 |
| 6 | compaction 794-914 | traveling 659-1349 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.08/s (thr 0.09), dlogR -0.18, dur 4.0s, P mean 0.82 min 0.73 (pre 0.84), 100% frames P>=0.65, speed x1.24 | P 0.82, M 0.2, dlogR -0.18 |
| 7 | compaction to expansion 914-959 | traveling 659-1349 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.69, M 0.39, dlogR 0.03 |
| 8 | expansion 959-1064 | traveling 659-1349 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.09), dlogR +0.28, dur 3.5s, P mean 0.74 min 0.66 (pre 0.67), 100% frames P>=0.65, speed x1.49 | P 0.74, M 0.34, dlogR 0.27 |
| 9 | expansion to traveling 1064-1109 | traveling 659-1349 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.92, M 0.14, dlogR 0.03 |
| 11 | traveling to compaction 1199-1229 | traveling 659-1349 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.93, M 0.06, dlogR -0.01 |
| 12 | compaction 1229-1349 | traveling 659-1349 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.05/s (thr 0.09), dlogR -0.16, dur 4.0s, P mean 0.90 min 0.82 (pre 0.93), 100% frames P>=0.65, speed x0.81 | P 0.9, M 0.05, dlogR -0.15 |
| 13 | compaction to milling 1349-1528 | traveling to milling 1349-1528 | transition renamed because neighbour was relabelled | P 0.67, M 0.45, dlogR -0.14 |
| 15 | milling to expansion 1873-1978 | milling to traveling 1873-1978 | transition renamed because neighbour was relabelled | P 0.35, M 0.5, dlogR 0.14 |
| 16 | expansion 1978-2068 | traveling 2023-2383 | strict exp/comp: -> traveling (not rapid; 63% frames steady traveling); peak dlogR/dt 0.07/s (thr 0.09), dlogR +0.15, dur 3.0s, P mean 0.69 min 0.54 (pre 0.49), 63% frames P>=0.65, speed x1.61 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.54/0.36 .. 0.74/0.11 | P 0.69, M 0.2, dlogR 0.15 |
| 17 | expansion to traveling 2068-2113 | traveling 2023-2383 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.54/0.36 .. 0.74/0.11 | P 0.91, M 0.03, dlogR -0.01 |
| 19 | traveling to compaction 2203-2248 | traveling 2023-2383 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.54/0.36 .. 0.74/0.11 | P 0.94, M 0.05, dlogR -0.04 |
| 20 | compaction 2248-2383 | traveling 2023-2383 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.07/s (thr 0.09), dlogR -0.27, dur 4.5s, P mean 0.88 min 0.74 (pre 0.94), 100% frames P>=0.65, speed x0.91 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.54/0.36 .. 0.74/0.11 | P 0.88, M 0.09, dlogR -0.26 |
| 21 | compaction to shoaling 2383-2502 | traveling to shoaling 2383-2502 | transition renamed because neighbour was relabelled | P 0.52, M 0.04, dlogR -0.13 |
| 29 | traveling to expansion 3776-3806 | traveling 3761-4211 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.57/0.08 .. 0.71/0.35 | P 0.75, M 0.25, dlogR 0.04 |
| 30 | expansion 3806-3881 | traveling 3761-4211 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.09/s (thr 0.09), dlogR +0.17, dur 2.5s, P mean 0.86 min 0.78 (pre 0.75), 100% frames P>=0.65, speed x1.79 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.57/0.08 .. 0.71/0.35 | P 0.86, M 0.24, dlogR 0.16 |
| 31 | expansion to compaction 3881-3926 | traveling 3761-4211 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.57/0.08 .. 0.71/0.35 | P 0.94, M 0.09, dlogR -0.04 |
| 32 | compaction 3926-4076 | traveling 3761-4211 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.09), dlogR -0.41, dur 5.0s, P mean 0.92 min 0.87 (pre 0.94), 100% frames P>=0.65, speed x1.05 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.57/0.08 .. 0.71/0.35 | P 0.92, M 0.07, dlogR -0.4 |
| 33 | compaction to traveling 4076-4136 | traveling 3761-4211 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.57/0.08 .. 0.71/0.35 | P 0.86, M 0.18, dlogR -0.05 |
| 38 | expansion 6144-6294 | traveling 6189-6653 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.07/s (thr 0.09), dlogR +0.23, dur 5.0s, P mean 0.77 min 0.56 (pre 0.52), 80% frames P>=0.65, speed x2.56 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.56/0.04 .. 0.67/0.02 | P 0.77, M 0.16, dlogR 0.22 |
| 39 | expansion to traveling 6294-6324 | traveling 6189-6653 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.56/0.04 .. 0.67/0.02 | P 0.91, M 0.13, dlogR 0.01 |
| 41 | traveling to compaction 6459-6503 | traveling 6189-6653 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.56/0.04 .. 0.67/0.02 | P 0.88, M 0.15, dlogR -0.05 |
| 42 | compaction 6503-6653 | traveling 6189-6653 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.07/s (thr 0.09), dlogR -0.28, dur 5.0s, P mean 0.80 min 0.67 (pre 0.88), 100% frames P>=0.65, speed x0.93 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.56/0.04 .. 0.67/0.02 | P 0.8, M 0.09, dlogR -0.27 |
| 45 | traveling to expansion 7133-7178 | traveling 6938-7582 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.64/0.42 | P 0.73, M 0.46, dlogR 0.02 |
| 46 | expansion 7178-7283 | traveling 6938-7582 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.11/s (thr 0.09), dlogR +0.26, dur 3.5s, P mean 0.83 min 0.76 (pre 0.74), 100% frames P>=0.65, speed x1.60 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.64/0.42 | P 0.83, M 0.26, dlogR 0.25 |
| 47 | expansion to traveling 7283-7328 | traveling 6938-7582 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.64/0.42 | P 0.94, M 0.07, dlogR -0.01 |
| 49 | traveling to compaction 7463-7507 | traveling 6938-7582 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.64/0.42 | P 0.88, M 0.22, dlogR -0.03 |
| 50 | compaction 7507-7582 | traveling 6938-7582 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.08/s (thr 0.09), dlogR -0.13, dur 2.5s, P mean 0.74 min 0.64 (pre 0.88), 93% frames P>=0.65, speed x0.88 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.64/0.42 | P 0.74, M 0.32, dlogR -0.13 |
| 51 | compaction to milling 7582-7642 | traveling to milling 7582-7642 | transition renamed because neighbour was relabelled | P 0.5, M 0.52, dlogR -0.04 |
| 55 | expansion to compaction 8272-8362 | expansion to traveling 8272-8362 | transition renamed because neighbour was relabelled | P 0.78, M 0.09, dlogR 0.06 |
| 56 | compaction 8362-8511 | traveling 8362-8661 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.09/s (thr 0.09), dlogR -0.34, dur 5.0s, P mean 0.88 min 0.80 (pre 0.86), 100% frames P>=0.65, speed x1.24 / split around new expansion 8781-8916 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -120 fr (-4.0s); edge P/M before trim 0.90/0.07 .. 0.46/0.58 | P 0.88, M 0.18, dlogR -0.33 |
| 57 | compaction to traveling 8511-8571 | traveling 8362-8661 | no state change left after neighbour relabel; 100% frames steady traveling / split around new expansion 8781-8916 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -120 fr (-4.0s); edge P/M before trim 0.90/0.07 .. 0.46/0.58 | P 0.78, M 0.3, dlogR -0.1 |
| 60 | expansion 8871-8976 | traveling 8916-9081 | strict exp/comp: -> traveling (not rapid; 69% frames steady traveling); peak dlogR/dt 0.08/s (thr 0.09), dlogR +0.22, dur 3.5s, P mean 0.70 min 0.55 (pre 0.53), 69% frames P>=0.65, speed x1.64 / split around new expansion 8781-8916 | P 0.7, M 0.32, dlogR 0.21 |
| 61 | expansion to traveling 8976-9006 | traveling 8916-9081 | no state change left after neighbour relabel; 100% frames steady traveling / split around new expansion 8781-8916 | P 0.84, M 0.2, dlogR -0.0 |
| 69 | traveling to compaction 10564-10594 | traveling 10490-11523 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.89, M 0.02, dlogR -0.02 |
| 70 | compaction 10594-10774 | traveling 10490-11523 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.10/s (thr 0.09), dlogR -0.41, dur 6.0s, P mean 0.90 min 0.83 (pre 0.89), 100% frames P>=0.65, speed x1.14 | P 0.9, M 0.24, dlogR -0.4 |
| 71 | compaction to traveling 10774-10819 | traveling 10490-11523 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.81, M 0.32, dlogR -0.07 |
| 73 | traveling to compaction 11344-11389 | traveling 10490-11523 | no state change left after neighbour relabel; 100% frames steady traveling | P 0.91, M 0.04, dlogR -0.05 |
| 74 | compaction 11389-11523 | traveling 10490-11523 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.06/s (thr 0.09), dlogR -0.23, dur 4.5s, P mean 0.85 min 0.72 (pre 0.92), 100% frames P>=0.65, speed x0.82 | P 0.85, M 0.07, dlogR -0.22 |
| 77 | traveling to expansion 11988-12033 | traveling 11703-12527 | no state change left after neighbour relabel; 87% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.86/0.02 | P 0.67, M 0.39, dlogR 0.05 |
| 78 | expansion 12033-12123 | traveling 11703-12527 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.09/s (thr 0.09), dlogR +0.22, dur 3.0s, P mean 0.81 min 0.71 (pre 0.67), 100% frames P>=0.65, speed x1.83 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.86/0.02 | P 0.81, M 0.25, dlogR 0.22 |
| 79 | expansion to traveling 12123-12153 | traveling 11703-12527 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.86/0.02 | P 0.93, M 0.07, dlogR 0.01 |
| 89 | traveling to compaction 13322-13367 | traveling 13232-13756 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.81/0.18 .. 0.63/0.41 | P 0.94, M 0.04, dlogR -0.08 |
| 90 | compaction 13367-13501 | traveling 13232-13756 | strict exp/comp: -> traveling (clear traveling); peak dlogR/dt 0.08/s (thr 0.09), dlogR -0.30, dur 4.5s, P mean 0.90 min 0.82 (pre 0.94), 100% frames P>=0.65, speed x0.98 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.81/0.18 .. 0.63/0.41 | P 0.9, M 0.08, dlogR -0.29 |
| 91 | compaction to traveling 13501-13546 | traveling 13232-13756 | no state change left after neighbour relabel; 100% frames steady traveling / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.81/0.18 .. 0.63/0.41 | P 0.79, M 0.24, dlogR -0.04 |
| 96 | expansion to compaction 15749-15854 | expansion to traveling 15749-15854 | transition renamed because neighbour was relabelled | P 0.8, M 0.3, dlogR -0.07 |
| 97 | compaction 15854-16049 | traveling 15854-15959 | strict exp/comp: -> traveling (not rapid; 62% frames steady traveling); peak dlogR/dt 0.09/s (thr 0.09), dlogR -0.48, dur 6.5s, P mean 0.67 min 0.49 (pre 0.79), 62% frames P>=0.65, speed x1.10 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -90 fr (-3.0s); edge P/M before trim 0.78/0.41 .. 0.49/0.49 | P 0.67, M 0.47, dlogR -0.48 |
| 98 | compaction to milling 16049-16094 | traveling to milling 16049-16094 | transition renamed because neighbour was relabelled | P 0.44, M 0.53, dlogR -0.05 |

### boundary_trim (5)

| old_seg | old | new | trimmed_s | reason | metrics |
|---|---|---|---|---|---|
| 24 | milling 2817-3432 | milling 3027-3432 | 7.0 | trimmed to steady milling (M>=0.50 & P<=0.50 held >= 1.0s at edges): start +210 fr (+7.0s), end +0 fr (+0.0s); edge P/M before trim 0.04/0.44 .. 0.12/0.54 | P 0.17, M 0.55, dlogR -0.04 |
| 35 | traveling 4615-5485 | traveling 4660-5485 | 1.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.58/0.50 .. 0.90/0.07 | P 0.81, M 0.36, dlogR -0.07 |
| 93 | traveling 15105-15450 | traveling 15210-15420 | 4.5 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +105 fr (+3.5s), end -30 fr (-1.0s); edge P/M before trim 0.53/0.11 .. 0.62/0.53 | P 0.66, M 0.35, dlogR -0.04 |
| 101 | traveling 16484-16588 | traveling 16513-16588 | 1.0 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +29 fr (+1.0s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.28 .. 0.71/0.32 | P 0.68, M 0.26, dlogR 0.06 |
| 106 | shoaling 17817-17999 | shoaling 17817-17952 | 1.6 | trimmed to steady shoaling (P<0.40 & M<0.40 held >= 1.0s at edges): start +0 fr (+0.0s), end -47 fr (-1.6s); edge P/M before trim 0.17/0.23 .. 0.11/0.21 | P 0.14, M 0.33, dlogR 0.23 |

### merged (16)

| old_seg | old | new | merged_with_orig | reason | metrics |
|---|---|---|---|---|---|
| 0 | traveling 120-360 | traveling 150-524 | 1;2 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +30 fr (+1.0s), end -30 fr (-1.0s); edge P/M before trim 0.59/0.11 .. 0.63/0.11 | P 0.82, M 0.18, dlogR 0.08 |
| 10 | traveling 1109-1199 | traveling 659-1349 | 4;5;6;7;8;9;11;12 | absorbed into a same-label neighbour after an adjacent relabel | P 0.95, M 0.05, dlogR -0.04 |
| 18 | traveling 2113-2203 | traveling 2023-2383 | 16;17;19;20 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.54/0.36 .. 0.74/0.11 | P 0.95, M 0.08, dlogR -0.05 |
| 28 | traveling 3716-3776 | traveling 3761-4211 | 29;30;31;32;33;34 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.57/0.08 .. 0.71/0.35 | P 0.64, M 0.15, dlogR -0.01 |
| 34 | traveling 4136-4211 | traveling 3761-4211 | 28;29;30;31;32;33 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.57/0.08 .. 0.71/0.35 | P 0.77, M 0.28, dlogR 0.01 |
| 40 | traveling 6324-6459 | traveling 6189-6653 | 38;39;41;42 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.56/0.04 .. 0.67/0.02 | P 0.9, M 0.13, dlogR -0.02 |
| 44 | traveling 6893-7133 | traveling 6938-7582 | 45;46;47;48;49;50 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.64/0.42 | P 0.73, M 0.3, dlogR 0.0 |
| 48 | traveling 7328-7463 | traveling 6938-7582 | 44;45;46;47;49;50 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.64/0.42 | P 0.93, M 0.07, dlogR -0.11 |
| 58 | traveling 8571-8826 | traveling 8362-8661 | 56;57 | split around new expansion 8781-8916 / trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -120 fr (-4.0s); edge P/M before trim 0.90/0.07 .. 0.46/0.58 | P 0.6, M 0.43, dlogR 0.06 |
| 62 | traveling 9006-9081 | traveling 8916-9081 | 60;61 | split around new expansion 8781-8916 | P 0.88, M 0.23, dlogR -0.06 |
| 68 | traveling 10490-10564 | traveling 10490-11523 | 69;70;71;72;73;74 | absorbed into a same-label neighbour after an adjacent relabel | P 0.73, M 0.08, dlogR 0.14 |
| 72 | traveling 10819-11344 | traveling 10490-11523 | 68;69;70;71;73;74 | absorbed into a same-label neighbour after an adjacent relabel | P 0.82, M 0.28, dlogR 0.28 |
| 76 | traveling 11658-11988 | traveling 11703-12527 | 77;78;79;80 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.86/0.02 | P 0.75, M 0.26, dlogR 0.05 |
| 80 | traveling 12153-12527 | traveling 11703-12527 | 76;77;78;79 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +45 fr (+1.5s), end +0 fr (+0.0s); edge P/M before trim 0.61/0.41 .. 0.86/0.02 | P 0.84, M 0.22, dlogR -0.16 |
| 88 | traveling 13232-13322 | traveling 13232-13756 | 89;90;91;92 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.81/0.18 .. 0.63/0.41 | P 0.89, M 0.08, dlogR -0.06 |
| 92 | traveling 13546-13786 | traveling 13232-13756 | 88;89;90;91 | trimmed to steady traveling (P>=0.65 held >= 1.0s at edges): start +0 fr (+0.0s), end -30 fr (-1.0s); edge P/M before trim 0.81/0.18 .. 0.63/0.41 | P 0.69, M 0.34, dlogR 0.0 |

### new_from_gap (5)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| milling | 02:29 | 02:32 | 4466-4555 | gap 4211-4615: 3.0s continuous steady milling; P 0.34, M 0.66 |
| shoaling | 03:17.5 | 03:23 | 5919-6084 | gap 5679-6144: 5.5s continuous steady shoaling; P 0.29, M 0.33 |
| milling | 07:48.5 | 08:05.5 | 14041-14550 | gap 13786-15105: 17.0s continuous steady milling; P 0.43, M 0.71 |
| shoaling | 08:19 | 08:22 | 14955-15045 | gap 13786-15105: 3.0s continuous steady shoaling; P 0.36, M 0.24 |
| shoaling | 09:27.5 | 09:45 | 17008-17532 | gap 16738-17577: 17.5s continuous steady shoaling; P 0.24, M 0.23 |

### new_event_in_segment (1)

| new_label | new_start | new_end | new_frames | reason / key metrics |
|---|---|---|---|---|
| expansion | 04:53 | 04:57.5 | 8781-8916 | strict rapid event (fast, polarization broken, speed burst): peak dlogR/dt 0.09/s (thr 0.09), dlogR +0.36, dur 4.7s, P mean 0.56 min 0.46 (pre 0.47), 12% frames P>=0.65, speed x1.38; carved from traveling |

### removed (4)

| old_seg | old | new | reason | metrics |
|---|---|---|---|---|
| 3 | compaction to expansion 554-659 | —  | transition traveling->traveling after neighbour relabel; only 42% steady | P 0.64, M 0.22, dlogR 0.08 |
| 43 | compaction to traveling 6653-6893 | —  | transition traveling->traveling after neighbour relabel; only 5% steady | P 0.6, M 0.17, dlogR 0.01 |
| 59 | traveling to expansion 8826-8871 | —  | transition traveling->traveling after neighbour relabel; only 0% steady | P 0.53, M 0.55, dlogR 0.12 |
| 75 | compaction to traveling 11523-11658 | —  | transition traveling->traveling after neighbour relabel; only 22% steady | P 0.62, M 0.34, dlogR -0.01 |

### unchanged (31)

Segments: 14, 22, 23, 25, 26, 27, 36, 37, 52, 53, 54, 63, 64, 65, 66, 67, 81, 82, 83, 84, 85, 86, 87, 94, 95, 99, 100, 102, 103, 104, 105.

Flagged (kept per rule 3, but a state neighbour was trimmed away, removed or relabelled; check): 23 (shoaling to milling), 26 (expansion), 54 (expansion), 82 (compaction), 86 (expansion), 95 (expansion), 104 (compaction).

