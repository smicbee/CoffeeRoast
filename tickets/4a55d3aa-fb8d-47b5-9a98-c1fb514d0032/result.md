# Result

Implemented the first working slice for the DIY Reproducible Coffee Roasting Platform idea.

## Summary

- Added firmware-side PWM clamping, `get status`, and failsafe behavior that turns the heater off and drives the fan to 255/255.
- Added iRoastControl preflight checks before the first heated run, including controller status validation and a safety checklist.
- Made recipe loading more reliable by resolving recipes from the application output folder first and handling missing recipe folders/files without crashing.
- Fixed control-loop startup and history-array bounds so first run, long roasts, and PID plotting stay inside allocated arrays.
- Documented the Windows build/run workflow, first-run calibration, controller status command, and failsafe behavior.

## Verification

- Built `iRoastControl Software/iRoastControl.sln` with `xbuild /p:Configuration=Debug /p:Platform="Any CPU"` successfully.
- Firmware source was reviewed, but not compiled because `arduino-cli` is not installed in this environment.
