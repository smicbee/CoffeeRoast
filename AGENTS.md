# Project: CoffeeRoast

## Description
A DIY coffee-roaster project that converts a hot-air popcorn machine into a reproducible roast-curve roaster using an ESP32-S3 firmware controller, MAX6675 thermocouple feedback, SSR heater PWM, fan control, KiCad hardware assets, documentation, and a C# WinForms application called iRoastControl for recipes, graphing, PID control, and serial communication.

## Current Idea
CoffeeRoast should become a practical open-source kit for coffee hobbyists who want repeatable small-batch roasting without buying a commercial machine. The project already combines hardware instructions, ESP32 firmware, Kaffeelogic-style recipe files, and the iRoastControl desktop UI. The next meaningful direction is to make the control loop trustworthy: fix startup/preheat behavior, align recipe parsing with the supplied `.kpro` profiles, harden serial/firmware safety boundaries, and make the Windows build reproducible so users can confidently assemble, flash, run, and tune their own roaster.

## Guidelines
- Commit all changes with descriptive messages
- Do not modify files outside this directory
- When completing a ticket, create `tickets/<ticket-id>/result.md` with a summary
- Follow existing code patterns in the repository
- Run tests if a test suite exists before submitting
- Keep changes focused on the assigned ticket

## Existing Tickets (do not duplicate)
- 🔍 [BUG/critical] Fix first-run roast startup crash (proposed)
- 🔍 [BUG/high] Correct the control-loop timer interval (proposed)
- 🔍 [BUG/high] Make preheating wait for the documented target temperature (proposed)
- 🔍 [BUG/high] Apply PID and targeting parameters from imported recipes (proposed)
- 🔍 [BUG/medium] Harden `.kpro` recipe parsing (proposed)
- 🔍 [BUG/medium] Make serial numeric commands culture-invariant and firmware-bounded (proposed)
- 🔍 [BUG/medium] Make manual PID settings actually update the controller (proposed)
- 🔍 [TASK/medium] Make the project build reproducibly from source (proposed)

