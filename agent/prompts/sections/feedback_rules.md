<repair_strategy>
- After each edit, the harness validates the artifact automatically. Do not ask for a separate compile step.
- Read `<summary>` first when the harness returns `<compile_signals>`.
- Treat `<failures>` as blocking; treat `<warnings>` as design evidence; treat `<notes>` as supporting context.
- Classify each bad result as a local implementation bug, a wrong geometric representation, a wrong overall composition, or a wrong proportion hierarchy.
- Fix failures at the right level: patch locally for local bugs, but rewrite geometry and tests together when the representation or composition is wrong.
- If the defect is about bulk, tallness, thinness, opening size, taper, shell thickness, setback, or feature dominance, edit the controlling profiles and dependent subassemblies together instead of nudging isolated dimensions.
- If the same failure class or weak hero features persist across two repair turns, stop patching locally and rewrite the affected region.
- If you have already spent multiple repair turns nudging positions, clearances, or primitive dimensions in one subassembly, stop tuning and replace that subassembly with a simpler, more realistic representation.
- If multiple repair turns touch the same region for proportion-related reasons, stop local tweaking and rewrite the envelope-driving geometry for that region.
- When the current geometry reads as a placeholder, do not preserve it just because it is close to passing QC. Rewrite it from the visual intent.
- Solve realism in this order unless the prompt clearly suggests otherwise: dominant silhouette, dominant openings/apertures, nested cavities or layers, then secondary detailing.
- When you add or change visible geometry or motion, update the prompt-specific tests in the same edit so the new claim is actually proved.
</repair_strategy>
