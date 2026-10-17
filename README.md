# Super Mario 3D Land — native 60 FPS preview

An experimental USA Rev 1 game-code patch for Azahar, a Windows installer, and one-click 4K60 recorders for ordinary 2D and side-by-side stereo.

## Install the game patch

1. Download and extract the Windows ZIP from Releases.
2. Close Azahar and open **patch/Mario 60 FPS Setup.exe**.
3. Choose your own matching USA Rev 1 `.3ds` file and Azahar installation, then click **Install 60 FPS**. The installer detects common profiles and recently played ROMs.
4. Start the game in Azahar at **100% speed**, with other FPS/interval cheats disabled.

The installer verifies the exact ROM SHA-256, generates the modified executable header from that ROM, and backs up replaced files. Use **Uninstall** in the same window to restore those files. ROMs, original game executables/headers, keys, saves, emulator binaries, recordings, and personal profiles are not distributed.

## Record gameplay

- **Record Mario 2D in Azahar.exe** opens a single non-stereoscopic view and records a normal **3840×2160, 60 FPS, 16:9** MP4 with audio.
- **Record Mario in Azahar.exe** records **3840×2160 combined half-SBS** with audio. Its **32:9 display-aspect tag** makes supporting players show the pair as a wide video. This is one combined 4K frame, not 4K per eye.

The launchers find a nearby portable Azahar installation or ask you to select it and your ROM on first use. Choices are stored locally in `recording-config.json`. The patch must already be installed. **Close the Azahar application to finalize the MP4 and save it to your Windows Desktop.** Merely stopping emulation while leaving the app open keeps recording. Both launchers restore recording-only graphics/layout settings afterward and preserve controller mappings and saves.

Requirements: Windows, a primary display set to **3840×2160**, an NVIDIA GPU with H.264 NVENC support, and FFmpeg with `ddagrab`/NVENC. FFmpeg is found beside the launcher, in Jellyfin Server's installation, or on PATH. FFmpeg and Azahar are not bundled.

Recording uses GPU Desktop Duplication of the primary desktop and WASAPI audio from the default Windows playback device. Other windows shown over the fullscreen game and other system sounds are included. The bottom/touch screen is not recorded. On Odyssey 3D systems running the Hub, the existing [dEPTH](https://github.com/AlonBorodAHub/dEPTH) Hub helper must confirm raw-output mode, suspending display conversion for recording. Close SR-Loom/SRWeaver before recording. Ordinary systems without that Hub do not need the helper.

## Compatibility and scope

Only **USA Rev 1**, title ID `0004000000054000`, is supported. Exact hashes are in `patch/manifest.json`. European/Chinese versions and other revisions need separate ports. The patch targets 60 Hz rendering through native ARM transform interpolation while retaining the original 30 Hz gameplay update cadence. No display/AI frame generation is used.

The tester confirmed smooth motion, working jumps and stereo depth, corrected map-camera motion, and disappearance of glove lag when jumping with camera movement. ARM checks include 720 rigid/unrelated model cases, 480 recorded body cases and 121 input cases. Local recorder tests verified launch → recording → emulator exit → saved MP4, AAC audio, and restoration of controller/graphics settings.

This remains a preview: complete game timing, every level, costume, enemy/effect and cutscene, performance on other PCs, and compatibility with other emulator builds are not comprehensively validated. Tested against the project's Azahar 2126.2 validation build; the patch and recorders have no RPC/debugger dependency. Downloaded builds still need first-use testing on the recipient's machine.

## Source and building

- `patch/source/`: installer UI and ARM assembly reference.
- `patch/research/`: native patch generators/tests. Original executable/header and some pose fixtures are private inputs and are not included; this is not a standalone ROM rebuilding kit.
- `recorders/`: 2D/SBS launchers, settings recovery and WASAPI capture source.
- `python recorders/build.py` builds both Windows launchers using the installed .NET Framework C# compiler.

The recorder's system-audio and raw-Hub handshake were adapted from this account's dEPTH recorder. No third-party emulator or FFmpeg code is bundled. This repository is unaffiliated with Nintendo or Azahar.
