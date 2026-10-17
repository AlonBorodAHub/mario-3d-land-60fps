using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

internal static class MarioRecorder {
#if MONO
    private const bool Stereo = false;
    private const string ModeName = "2D", Aspect = "16:9";
#else
    private const bool Stereo = true;
    private const string ModeName = "SBS", Aspect = "32:9";
#endif
    private const string RequestEvent = @"Local\dEPTH.RawSbsRecordingRequested";
    private const string ReadyEvent = @"Local\dEPTH.HubRawSbsReady";
    private static readonly string Root = AppDomain.CurrentDomain.BaseDirectory;
    [DllImport("user32.dll")] private static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] private static extern bool AllowSetForegroundWindow(uint id);
    [DllImport("user32.dll")] private static extern bool SetWindowPos(IntPtr handle, IntPtr after, int x, int y, int width, int height, uint flags);
    [STAThread] private static int Main(string[] args) {
        SetProcessDPIAware();
        Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
        bool test = args.Length > 0;
        try {
            bool created;
            using (var mutex = new Mutex(true, @"Local\Mario3DLand.RawSbsRecorder", out created)) {
                if (!created) throw new InvalidOperationException("The Mario recorder is already running.");
                if (args.Length == 2 && args[0] == "--self-test") {
                    RecordSettings.Test(args[1], Stereo);
                    var screen = Screen.PrimaryScreen.Bounds;
                    File.WriteAllText(Path.Combine(args[1], "self-test.txt"), ModeName + " settings apply/restore/recovery passed.\r\nPrimary display: " + screen.Width + "x" + screen.Height + "\r\nFFmpeg: " + FindFfmpeg());
                    return 0;
                }
                if (Process.GetProcessesByName("azahar").Length != 0) throw new InvalidOperationException("Close the existing Azahar window, then open Record Mario in Azahar again. Your current game has been left running.");
                RecordSettings.Recover(Path.Combine(Root, "recorder", "settings-recovery.json"));
                string output = Unique(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "Super Mario 3D Land - " + ModeName + " 4K60 - " + DateTime.Now.ToString("yyyy-MM-dd HH-mm-ss") + ".mp4"));
                int testSeconds = 0;
                if (args.Length == 3 && args[0] == "--test-session") { output = Path.GetFullPath(args[1]); testSeconds = Math.Max(2, int.Parse(args[2])); }
                else if (args.Length != 0) throw new ArgumentException("Unknown recorder arguments.");
                Capture(output, testSeconds);
                if (!test) MessageBox.Show("Your " + ModeName + " 4K 60 FPS video is saved:\n\n" + output, "Mario recording saved", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return 0;
            }
        } catch (Exception ex) {
            string log = Path.Combine(Root, "recorder", "last-error.txt");
            try { Directory.CreateDirectory(Path.GetDirectoryName(log)); File.WriteAllText(log, ex.ToString()); } catch { }
            if (!test) MessageBox.Show(ex.Message + "\n\nDetails: " + log, "Mario recording", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
    private static string Hash(string file) {
        using (var stream = File.OpenRead(file)) using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
    }
    internal static string Quote(string value) {
        return "\"" + Regex.Replace(Regex.Replace(value, "(\\\\*)\"", "$1$1\\\""), "(\\\\+)$", "$1$1") + "\"";
    }
    private static string Unique(string file) {
        if (!File.Exists(file)) return file;
        for (int i = 2; ; i++) { string candidate = Path.Combine(Path.GetDirectoryName(file), Path.GetFileNameWithoutExtension(file) + " (" + i + ")" + Path.GetExtension(file)); if (!File.Exists(candidate)) return candidate; }
    }
    private static string FindFfmpeg() {
        foreach (string path in new [] { Path.Combine(Root, "ffmpeg.exe"), Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), @"Jellyfin\Server\ffmpeg.exe") }) if (File.Exists(path)) return path;
        foreach (string folder in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(Path.PathSeparator)) {
            try { string path = Path.Combine(folder.Trim().Trim('"'), "ffmpeg.exe"); if (File.Exists(path)) return path; } catch { }
        }
        throw new FileNotFoundException("FFmpeg was not found. This launcher uses the same FFmpeg installation as dEPTH Record (Jellyfin Server), or ffmpeg.exe placed beside this launcher.");
    }
    private static Process Start(string executable, string args, string log, bool input) {
        var info = new ProcessStartInfo(executable, args) { UseShellExecute = false, CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden, RedirectStandardError = true, RedirectStandardInput = input };
        var process = new Process { StartInfo = info };
        process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) { if (e.Data != null) { try { lock (log) File.AppendAllText(log, e.Data + Environment.NewLine); } catch { } } };
        if (!process.Start()) throw new IOException("Could not start " + Path.GetFileName(executable));
        process.BeginErrorReadLine(); return process;
    }
    private static string Tail(string file) { try { string text = File.ReadAllText(file); return text.Length > 2000 ? text.Substring(text.Length - 2000) : text; } catch { return "Recording log unavailable."; } }
    private static void ProbeEncoder(string ffmpeg, string log) {
        using (var process = Start(ffmpeg, "-hide_banner -loglevel error -f lavfi -i color=size=256x256:rate=1 -frames:v 1 -c:v h264_nvenc -f null NUL", log, false)) {
            if (!process.WaitForExit(10000)) { process.Kill(); throw new IOException("NVIDIA encoder did not respond."); }
            if (process.ExitCode != 0) throw new IOException("NVIDIA hardware video encoding is unavailable.\n" + Tail(log));
        }
    }
    private static EventWaitHandle EnableRawSbs() {
        foreach (string name in new [] { "SRLoom", "SR-Loom", "SRWeaver" }) {
            if (Process.GetProcessesByName(name).Length != 0) throw new InvalidOperationException("Close SR-Loom/SRWeaver before recording so the file contains the original left and right pictures.");
        }
        var request = new EventWaitHandle(false, EventResetMode.ManualReset, RequestEvent); request.Set();
        try {
            if (Process.GetProcessesByName("Odyssey3DHubService").Length != 0) {
                if (Process.GetProcessesByName("HubSessionGuard").Length == 0) throw new InvalidOperationException("The dEPTH Hub helper is not running. Start the existing dEPTH Hub helper before recording, or turn off Odyssey Hub video conversion.");
                var timer = Stopwatch.StartNew(); bool ready = false;
                while (timer.ElapsedMilliseconds < 15000) {
                    try { using (var signal = EventWaitHandle.OpenExisting(ReadyEvent)) { if (signal.WaitOne(200)) { ready = true; break; } } }
                    catch (WaitHandleCannotBeOpenedException) { Thread.Sleep(200); }
                }
                if (!ready) throw new TimeoutException("The dEPTH Hub helper did not confirm raw side-by-side mode. No recording was started.");
            }
            return request;
        } catch { request.Reset(); request.Dispose(); throw; }
    }
    private static void StopVideo(Process process) {
        if (!process.HasExited) {
            process.StandardInput.WriteLine("q"); process.StandardInput.Flush();
            if (!process.WaitForExit(15000)) { process.Kill(); process.WaitForExit(); throw new IOException("Video recording did not stop cleanly. The temporary recording has been kept."); }
        }
        if (process.ExitCode != 0) throw new IOException("The video encoder stopped with an error. The temporary recording has been kept.");
    }
    private static void WaitForGameWindow(Process game) {
        var clock = Stopwatch.StartNew();
        while (clock.ElapsedMilliseconds < 30000) {
            if (game.HasExited) throw new IOException("Azahar closed before recording started.");
            game.Refresh();
            if (game.MainWindowHandle != IntPtr.Zero) {
                var bounds = Screen.PrimaryScreen.Bounds;
                SetWindowPos(game.MainWindowHandle, IntPtr.Zero, bounds.X, bounds.Y, bounds.Width, bounds.Height, 0x0044);
                Thread.Sleep(1500); return;
            }
            Thread.Sleep(100);
        }
        throw new TimeoutException("Azahar did not open its game window.");
    }
    private static void Capture(string output, int testSeconds) {
        var configuration = PortableConfiguration.Load(Root);
        string ffmpeg = FindFfmpeg(), emulator = configuration.Emulator, user = configuration.UserDirectory, rom = configuration.Rom;
        var json = new JavaScriptSerializer();
        var manifest = json.Deserialize<Dictionary<string, object>>(File.ReadAllText(Path.Combine(Root, "patch", "manifest.json")));
        if (Hash(rom) != (string)manifest["rom_sha256"])
            throw new InvalidOperationException("This ROM does not match USA Rev 1. To choose a different ROM, remove recording-config.json beside this launcher and start it again.");
        string mods = Path.Combine(user, "load", "mods", "0004000000054000");
        if (!File.Exists(Path.Combine(mods, "exefs", "code.ips")) || Hash(Path.Combine(mods, "exefs", "code.ips")) != (string)manifest["patch_sha256"] || !File.Exists(Path.Combine(mods, "exheader.bin")) || Hash(Path.Combine(mods, "exheader.bin")) != (string)manifest["patched_exheader_sha256"])
            throw new InvalidOperationException("Install the Mario 60 FPS patch first: open patch/Mario 60 FPS Setup.exe.");
        string session = Path.Combine(Root, "recorder", "sessions", DateTime.Now.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(session);
        string video = Path.Combine(session, "video.mkv"), audio = Path.Combine(session, "audio.wav"), mp4 = Path.Combine(session, "finished.mp4"), log = Path.Combine(session, "recording.log");
        var settings = new RecordSettings(Path.Combine(Root, "recorder", "settings-recovery.json"));
        EventWaitHandle raw = null; Process game = null, recorder = null; LoopbackCapture loopback = null;
        bool configured = false, finished = false;
        try {
            Rectangle screen = Screen.PrimaryScreen.Bounds;
            if (screen.Width != 3840 || screen.Height != 2160) throw new InvalidOperationException("The recording screen must be set to 3840 x 2160. Current primary screen: " + screen.Width + " x " + screen.Height + ".");
            ProbeEncoder(ffmpeg, Path.Combine(session, "encoder-probe.log"));
            raw = EnableRawSbs();
            configured = true; settings.Apply(user, session, Stereo);
            game = Process.Start(new ProcessStartInfo(emulator, Quote(rom)) { UseShellExecute = false, WorkingDirectory = Path.GetDirectoryName(emulator) });
            AllowSetForegroundWindow((uint)game.Id); WaitForGameWindow(game);
            loopback = new LoopbackCapture(audio); loopback.Start();
            string capture = "-hide_banner -loglevel info -stats_period 1 -y -f lavfi -i ddagrab=output_idx=0:draw_mouse=0:framerate=60:video_size=3840x2160:dup_frames=true -an -c:v h264_nvenc -preset p1 -tune ull -rc constqp -qp 21 -zerolatency 1 -r 60 -fps_mode cfr -aspect " + Aspect + " -f matroska " + Quote(video);
            recorder = Start(ffmpeg, capture, log, true);
            var running = Stopwatch.StartNew();
            while (!game.WaitForExit(150)) {
                if (recorder.HasExited) throw new IOException("Screen recording stopped unexpectedly.\n" + Tail(log));
                if (testSeconds > 0 && running.Elapsed.TotalSeconds >= testSeconds) {
                    game.CloseMainWindow();
                    if (!game.WaitForExit(15000)) throw new IOException("Azahar did not close after the recording test. It has been left running.");
                }
            }
            StopVideo(recorder); recorder.Dispose(); recorder = null;
            loopback.Stop(); loopback.Dispose(); loopback = null;
            if (!File.Exists(video) || new FileInfo(video).Length < 1024) throw new IOException("No usable video was captured.\n" + Tail(log));
            if (!File.Exists(audio) || new FileInfo(audio).Length < 64) throw new IOException("System audio was not captured.");
            string muxArgs = "-hide_banner -loglevel warning -y -i " + Quote(video) + " -i " + Quote(audio) + " -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -af aresample=async=1:first_pts=0 -shortest -movflags +faststart -metadata title=" + Quote("Super Mario 3D Land - " + ModeName + " 4K60") + " " + Quote(mp4);
            using (var mux = Start(ffmpeg, muxArgs, log, false)) {
                if (!mux.WaitForExit(180000)) { mux.Kill(); throw new TimeoutException("Finishing the MP4 took too long. Original recordings are kept in " + session); }
                if (mux.ExitCode != 0 || !File.Exists(mp4)) throw new IOException("The MP4 could not be finished.\n" + Tail(log));
            }
            Directory.CreateDirectory(Path.GetDirectoryName(output));
            if (File.Exists(output)) throw new IOException("Output already exists; recorded files were kept in " + session);
            File.Move(mp4, output); finished = true;
            File.WriteAllText(Path.Combine(session, "result.json"), json.Serialize(new { output = output, width = 3840, height = 2160, fps = 60, display_aspect = Aspect, stereoscopic = Stereo, capture = ModeName + " desktop duplication, NVIDIA NVENC", saved_on_emulator_exit = true }));
        } catch (Exception ex) { throw new IOException(ex.Message + "\n\nRecording/recovery folder: " + session, ex); }
        finally {
            if (recorder != null) { try { StopVideo(recorder); } catch { } recorder.Dispose(); }
            if (loopback != null) { try { loopback.Stop(); } catch { } loopback.Dispose(); }
            if (raw != null) { raw.Reset(); raw.Dispose(); }
            if (configured && (game == null || game.HasExited)) settings.Restore();
            if (game != null) game.Dispose();
            if (finished) { if (File.Exists(video)) File.Delete(video); if (File.Exists(audio)) File.Delete(audio); }
        }
    }
}
