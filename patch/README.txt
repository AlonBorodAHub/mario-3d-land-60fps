Super Mario 3D Land - native 60 FPS rendering preview 0.2
USA Rev 1 / title 0004000000054000 / Windows + Azahar

WHAT TO SHARE
Send this entire ZIP. It contains a game-code patch and installer, without the
ROM, original executable, original header, emulator, saves or personal settings.
Each recipient supplies their own matching ROM and an Azahar installation.

INSTALL
1. Extract the ZIP to an ordinary folder. Close Azahar.
2. Double-click Mario 60 FPS Setup.exe. It opens a normal Windows window.
3. The window detects nearby portable Azahar installations and the Windows
   Azahar profile, and looks for Mario in Azahar's recent games. If necessary,
   use Browse beside Your game to pick the ROM, or Browse beside Azahar to
   pick azahar.exe.
   Click Install 60 FPS. No typed paths or terminal commands are needed.
   Choose data folder is an optional fallback for unusual installations.
4. The installer verifies SHA-256, builds the modified executable header from
   your ROM, and installs these two files:
   <user>/load/mods/0004000000054000/exheader.bin
   <user>/load/mods/0004000000054000/exefs/code.ips
5. Open Azahar and start the game normally. Keep emulation speed at 100%.
   Disable other FPS/interval cheats for this title to avoid conflicting writes.
   If a game update changes the executable, disable that update for this build.

Check ROM.cmd verifies compatibility without installing anything.
Use Uninstall in the same window to restore files replaced by this package.
Other mods, graphics settings, controller bindings, ROM and saves are untouched.
Existing versions of these two mod files are backed up before installation;
they are replaced, not merged. Keep the backup and installation record together.

COMPATIBILITY
Only the exact USA Rev 1 dump identified in manifest.json is accepted. Its
multilingual label is En,Fr,Es. Other dumps, encrypted copies, European/Chinese
versions, other revisions and installed-title formats are not accepted by this
installer. A European ROM needs a separate port of the patch.
Tested with the project's Azahar 2126.2 validation build. Use of an independently
installed Azahar build, and a fresh startup of this final integrated package,
still need recipient testing. The patch itself has no RPC/debugger dependency.

WHAT THE PATCH DOES
Targets 60 Hz rendered motion using native ARM game-code interpolation of
rendering transforms, with the original 30 Hz gameplay update cadence. Includes
input trigger retention, active-camera stereo handling, and separate rigid
glove-model motion correction. No display/AI frame generation is required.
The emulator FPS counter alone does not prove 60 distinct motion frames.

3D DISPLAY (OPTIONAL)
The patch can be used in normal 2D. For the tested Odyssey 3D setup, Azahar used
plain Side by Side at 30% depth, with right-eye rendering enabled, matched to
the display software's HalfSBS input. Display software and configuration are
not included. Configure your own screen and controller normally.

VALIDATION AND LIMITS
The tester confirmed smooth motion, normal-feeling gameplay, working jumps,
stereo depth, corrected map-camera movement, and disappearance of glove lag
when jumping with camera movement. Integrated ARM checks cover 720 rigid and
unrelated model cases, 480 recorded body cases, 121 input cases, plus camera,
cache lifetime and native dispatcher checks. Live glove captures match expected
midpoint/current positions without changing simulation transforms.
This is a preview, not a fully validated game-wide release. Final-build cold
startup, all levels, enemies/effects, cutscenes, powerups/costumes, performance
on other PCs and complete timing correctness are not comprehensively tested.
For first use, enter World 1-1, check jumps and camera motion, then test a return
to course selection. Report game region/revision, Azahar build, graphics mode,
level and the behavior observed.
