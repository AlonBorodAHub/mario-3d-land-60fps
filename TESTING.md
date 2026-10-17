# Validation checkpoint

- Native ARM validation: 720 rigid/unrelated model render cases, 480 recorded body render cases, 121 input-latch cases, 32 untouched native dispatcher cases, plus camera, cache lifecycle and flag-preservation checks.
- Original tester: smooth motion, working controls/jumps, Odyssey stereo depth, map-camera stutter fixed, and glove lag during jumps with camera movement disappeared.
- Windows installer: matching original ROM/header verification, ROM-file/folder input, clean install/remove, backup/restore of pre-existing patch files, duplicate installation rejection and protection of modified installed files.
- 2D and SBS recorders: automatic Azahar launch, 3840×2160 H.264 video with `60/1` frame rate, stereo AAC audio, final MP4 saved when Azahar exits, and original layout/controller settings restored.
- The exported portable 2D recorder was separately exercised through launch → record → close → saved file after replacing machine-specific paths with recipient configuration.

The short recorder checks used the game's opening/title sequence. They establish recorder operation and output format, not complete gameplay or full-game timing correctness. Other PCs/emulator builds, all levels/costumes/effects and longer sessions remain unverified. The preview's complete limitations are in README.md and patch/README.txt.
