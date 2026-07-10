# Hermes Agent Team — CoffeeRoast PCB RevA.1

Created: 2026-07-05
Board: `coffeeroast-pcb`
Project: `coffeeroast`
Workspace: `/home/smicbee/CoffeeRoast`
PCB project: `/home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA`

## Goal
Coordinate the RevA.1 PCB/PCBA decision around the current JLC Standard-PCBA cart item: keep conservative partial PCBA, move to a larger/max PCBA set, or defer risky parts to RevA.2.

Hard gates:
- No checkout/payment without explicit user approval.
- No credential/secret output.
- 230VAC remains off-board; this PCB is low-voltage controller only.
- JLC preview/orientation must be checked before ordering.

## Cards / roles

| Card | Role | Status at creation | Output |
|---|---|---|---|
| `t_7960ea98` | Footprint Auditor | running | `production/partial-smd-pcba/assembly/max_pcba_footprint_audit.md` |
| `t_cde7e0de` | Fabrication QA | running | `production/fabrication_qa_current.md` |
| `t_de3f898f` | Visual QA | running | `docs/pcb_visual_review.md` plus updated PNG renders |
| `t_956de182` | Safety/Power Reviewer | running | `docs/reva1_safety_power_review.md` |
| `t_ea9d4e7c` | PCBA BOM Engineer | waits for Footprint Auditor | `production/partial-smd-pcba/assembly/max_pcba_proposal.md` |
| `t_a3c78583` | JLC Handoff Agent | waits for Footprint + BOM | `production/jlc_partial_vs_max_handoff.md` |
| `t_7cc5beed` | Team Lead/Synthesizer | waits for all worker outputs | final decision brief |

## Dependency graph

```text
Footprint Auditor ─┬─> PCBA BOM Engineer ─┬─> JLC Handoff Agent ─┐
                   └──────────────────────┴──────────────────────┤
Fabrication QA ───────────────────────────────────────────────────┤
Visual QA ────────────────────────────────────────────────────────┤
Safety/Power Reviewer ────────────────────────────────────────────┤
                                                                  v
                                                    Team Lead/Synthesizer
```

## Useful commands

```bash
hermes kanban --board coffeeroast-pcb list
hermes kanban --board coffeeroast-pcb stats
hermes kanban --board coffeeroast-pcb show t_7960ea98
hermes kanban --board coffeeroast-pcb log t_7960ea98
hermes kanban --board coffeeroast-pcb runs t_7960ea98
hermes kanban --board coffeeroast-pcb dispatch --dry-run
hermes kanban --board coffeeroast-pcb dispatch --max 4
```

Notes:
- The board initially spawned every ready card; dependent cards `t_ea9d4e7c`, `t_a3c78583`, and `t_7cc5beed` were reclaimed and parked in `todo` with dependency waits so they resume only after parent outputs exist.
- All workers use the `electronics-pcb-design-workflows` skill.
