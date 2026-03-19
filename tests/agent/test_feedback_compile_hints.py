from __future__ import annotations

from agent.feedback import build_compile_signal_bundle, render_compile_signals


def test_compile_signal_bundle_includes_loft_hint() -> None:
    exc = RuntimeError(
        "ValueError: Loft profile area must be non-zero in XY projection; "
        "profiles should usually be closed XY loops at constant z"
    )
    rendered = render_compile_signals(build_compile_signal_bundle(status="failure", exc=exc))

    assert "<compile_signals>" in rendered
    assert "Loft profile area must be non-zero in XY projection" in rendered
    assert "Hint: LoftGeometry checks profile area in the XY projection." in rendered
    assert "author it in XY first and rotate the mesh afterward" in rendered
