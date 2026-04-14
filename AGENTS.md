# Project: CoffeeRoast

## Description
CoffeeRoast is a DIY coffee roaster project that converts a popcorn machine into a temperature-controlled roaster using an ESP32, thermocouple, solid-state relay, fan control, and a Windows iRoastControl application. It includes firmware, hardware documentation, KiCAD resources, and roast recipe/profile files for reproducible roasting curves.

## Current Idea
CoffeeRoast helps home roasters and hardware tinkerers turn an inexpensive popcorn machine into a controllable coffee roaster with repeatable roast curves. The project combines ESP32 firmware for temperature, relay, fan, and failsafe control with a Windows control app and shared roast profiles. The next meaningful direction is to tighten the end-to-end roasting workflow by improving setup documentation, validating safety behavior, and making the control software easier to run and calibrate for new builds.

## Guidelines
- Commit all changes with descriptive messages
- Do not modify files outside this directory
- When completing a ticket, create `tickets/<ticket-id>/result.md` with a summary
- Follow existing code patterns in the repository
- Run tests if a test suite exists before submitting
- Keep changes focused on the assigned ticket

## Existing Tickets (do not duplicate)
- 📋 [BUG/high] Fix control loop timer interval scaling (open)
- 🔍 [BUG/high] Make firmware failsafe fan behavior match the documented safety behavior (proposed)
- 🔍 [BUG/high] Add bounds checks before writing PID history arrays (proposed)
- 🔍 [BUG/medium] Clamp fan speed command output to firmware PWM range (proposed)
- 🔄 [IMPROVEMENT/medium] Document how to build and run the Windows control application (in_progress)
- 🔍 [TASK/medium] Add first-run serial calibration and safety checklist to setup docs (proposed)
- 🔍 [TASK/low] No actionable suggestion found (proposed)

## Active Task
**Document how to build and run the Windows control application** [improvement/medium]

The repository includes `iRoastControl Software/iRoastControl.sln` and `iRoastControl Software/iRoastControl.csproj`, but the README excerpt focuses on hardware setup and does not show the Windows app build/run workflow. Add a concise setup section covering required Visual Studio/.NET Framework version, NuGet package restore, solution path, serial connection expectations, and where roast recipes are loaded from.

When finished, write your summary to `tickets/371854d3-76b9-40a4-a5ea-a08362c73e47/result.md`
