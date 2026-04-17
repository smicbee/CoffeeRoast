# Result

Added a concise Windows setup section to `README.md` for the iRoastControl application.

## Summary

- Documented that `iRoastControl Software/iRoastControl.sln` is a Windows Forms app targeting .NET Framework 4.7.2.
- Listed the Visual Studio 2022 `.NET desktop development` workload and .NET Framework 4.7.2 targeting/developer pack requirement.
- Added first-run build steps, including NuGet package restore for `packages.config`.
- Documented the serial connection behavior: COM port auto-scan, `115200` baud, `hello` probe, and expected `popcorn roaster` firmware response.
- Documented where `.kpro` roast recipes are loaded from and how they are copied into the build output.

## Verification

- Inspected the solution, project file, package config, serial communication code, firmware serial commands, and recipe loading code to keep the documentation aligned with the implementation.
