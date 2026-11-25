# 140 - Roll-back check, and 5 random check marines (Nov 25)

Josh, before moving on: "build 5 random marines using only the bits that we have approved so far across multiple
makers", to check that nothing has rolled back.

## 1. History check: no roll-backs

The check went through every library commit since stage 1 (b64b58fc, 17 commits). It took every joint written from a
batch: a socket with `props.kb_josh`, or a fit listed in `exact`, including those in variants. Each was compared with
its first written value and with the library on D: today.

Result: **701 joints, 0 changed or gone.**

## 2. Five random check marines (`make_check_marines.py`)

`~\Desktop\mar fil connectors\batches\Check - 5 random marines (2026-11-25).blend`, seed 2374. Every piece is a locked
check piece, placed from the library alone (socket . fit, as TIOW does it).

**Approved** means written from Josh's batches. The torsos must not be hidden in the builder. That gives:
- 48 torsos (Josh has also hidden 15 TN torsos);
- 24 right arms (Arm 2B R and the 23 Assault arms);
- 17 cloaks;
- the guide and Shoulder Pad 1, only on Arm 2B R: no other arm's Pad R is approved yet;
- Helmet 1, Back Pack 1 and Legs 1A.

| # | Torso | Arm | Cloak |
|---|---|---|---|
| 1 | Mar Fil Outrider Torso B | Arm 2B R, with its pad | Marta Aug 2025 Cloak 5 (scaled), on Cloak Plain |
| 2 | TN Mk6 Assault Torso Universal A2 | Arm 8B R | Marta Aug 2025 Cloak 4 (scaled), on Cloak Plain |
| 3 | Redwarden Prime Techmarine Torso | Arm 4A R | CyberBrush Cloak 2, on Cloak |
| 4 | TN Mk8 Torso G1 | Arm 6B R | Marta 49 March Cloak 3, on Cloak Plain |
| 5 | Mar Fil Techmarine Chest | Arm 8A R | Marta 49 March Cloak 1, on Cloak Plain |

Renders from the front and back: every piece sits as approved. Each torso is used once (the first build picked one
twice; fixed).
