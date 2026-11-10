**Decided 17 Oct 2026: one connection point per joint, with each creator's correction baked into the origin at import.** This covers arms, heads, pauldrons and backpacks.

**The waist is the exception.** Mar Fil sculpts the belly armour on the legs, not the torso, so his waist is a different joint, not a correction. It is modelled as two joint families:
- `waist_mar`: Mar Fil torso ↔ Mar Fil legs.
- `waist_std`: any non-Mar torso ↔ any non-Mar legs, after corrections.

Cross-family:
- **Mar torso on other legs:** the filler piece Josh already uses, treated as an adapter. It sits on `waist_std` and carries a `waist_mar` socket.
- **Other torso on Mar legs:** one cross offset type, captured once and chained against the Mar legs' waist socket.

That makes a 2×2 waist setup however many creators there are, unless a third waist style turns up. The captured `Adaptor` fit type in the example file may be the filler; to confirm.
