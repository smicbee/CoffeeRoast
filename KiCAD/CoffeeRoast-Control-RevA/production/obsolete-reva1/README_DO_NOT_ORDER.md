# Obsolete RevA.1 manufacturing files

**Do not upload or order anything in this directory.**

These files describe the superseded two-stage `24V → 5V → 3.3V` power tree with U3 and a 5V SSR rail. RevA.2 removes U3 and +5V, uses one `24V → 3.3V` converter, and supplies the external SSR input from 3.3V.

Use only the freshly generated files under `../partial-smd-pcba/` after reviewing the exact U4 24V→3.3V module footprint and confirming that the selected SSR reliably triggers at 3.3V.
