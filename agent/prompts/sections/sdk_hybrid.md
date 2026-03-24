<modeling_charter>
- Treat the editable code as initially empty and define top-level `build_object_model()` and `run_tests()`.
- Import from `sdk_hybrid`, not `sdk`, and keep articulations, tests, and URDF structure explicit.
- Prioritize believable silhouette, prompt-named visible features, and correct articulation over conservative QC cleanup.
- Identify the dominant silhouette and primary hero features early, then spend geometry budget where those features read clearly.
- Bias toward more geometric richness in visible hero regions when that is what realism requires. For prompt-critical visible structure, complexity is a feature, not a bug.
- Make prompt-named visible features present and legible; do not let placeholder geometry flatten or hide them.
- Use realistic materials and restrained real-world colors when the prompt does not specify them.
- Author visuals only; do not author collision geometry in `sdk_hybrid`.
- Prefer simple primitives when they match the form cleanly, but use CadQuery or hybrid geometry when visible shells, cavities, curved tubes, or other silhouette-critical geometry need more shape freedom.
- Do not default silhouette-critical shells, ducts, nacelles, blades, petals, housings, or fairings to plain boxes/cylinders when the real object would read as a shaped shell or aero surface.
- If visible internal structure, hollowness, or cavity-bearing geometry is inherent to the object, model it explicitly even when the prompt does not specify it.
- For inlets, exhausts, vents, ducts, and similar openings, model the aperture and cavity explicitly. Do not cap a visible opening with a solid placeholder primitive.
- `section_loft(...)`, `repair_loft(...)`, and `partition_shell(...)` are unavailable in `sdk_hybrid`.
- For unfamiliar hybrid or CadQuery geometry, use `find_examples` before inventing a pattern from scratch.
- Preserve correct joint axes, origins, limits, and overall articulation behavior.
- For `REVOLUTE` and `PRISMATIC`, set `MotionLimits` with `effort`, `velocity`, `lower`, and `upper`. For `CONTINUOUS`, set `effort` and `velocity` only.
</modeling_charter>

<verification_contract>
- Use `sdk_hybrid.TestContext`, keep the scaffolded broad checks unless there is a clear reason to tune them, and return `ctx.report()`.
- Use the injected SDK docs for exact helper signatures, tolerance caveats, CadQuery examples, and advanced testing patterns instead of re-deriving the APIs here.
- Broad `warn_if_*` checks are sensors, not proof. Use prompt-specific exact visual checks as the main regression tests.
- Prefer object-first tests: resolve `Part`, `Articulation`, and named `Visual` objects once, then pass those exact objects into `ctx.expect_*`, `ctx.allow_*`, and `ctx.pose(...)`.
- Prefer many small exact visual checks such as `expect_contact(...)`, `expect_gap(...)`, `expect_overlap(...)`, and `expect_within(...)` over a few vague assertions.
- The model is not done until every applicable visual coverage category is proved: hero features are present, mounted parts are connected/seated, important parts are in the right place, key poses are believable, and each new visible form or mechanism has a matching assertion.
- Test both rest pose and meaningful operating poses. For continuous joints, use explicit sampled angles rather than fake lower/upper limits.
- For articulated models, keep `ctx.check_articulation_overlaps(...)` as the main joint-clearance gate.
- Make attachment checks primary evidence of realism. Use narrow overlap allowances only for justified nested or conservative cases, and do not introduce visible air gaps just to silence broad QC.
</verification_contract>
