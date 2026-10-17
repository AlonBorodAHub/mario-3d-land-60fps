using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows.Forms;

internal sealed class AzaharLocation {
    public string UserDirectory;
    public string Label;
    public override string ToString() { return Label; }
}

internal static class SetupPaths {
    public static bool IsUserDirectory(string path) {
        return Directory.Exists(path) && Directory.Exists(Path.Combine(path, "config")) &&
            (Directory.Exists(Path.Combine(path, "sdmc")) || Directory.Exists(Path.Combine(path, "load")));
    }
    public static List<AzaharLocation> Find(string start) {
        var result = new List<AzaharLocation>();
        var ancestor = new DirectoryInfo(start);
        for (int depth = 0; ancestor != null && depth < 6; depth++, ancestor = ancestor.Parent) {
            foreach (string relative in new [] { "user", "Azahar-validation/user", "Azahar/user" })
                Add(result, Path.Combine(ancestor.FullName, relative.Replace('/', Path.DirectorySeparatorChar)));
        }
        foreach (var root in new [] { Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData) }) {
            if (!String.IsNullOrEmpty(root)) Add(result, Path.Combine(root, "Azahar"));
        }
        return result;
    }
    public static void Add(List<AzaharLocation> result, string path) {
        if (!IsUserDirectory(path)) return;
        path = Path.GetFullPath(path);
        if (result.Any(x => String.Equals(x.UserDirectory, path, StringComparison.OrdinalIgnoreCase))) return;
        bool portable = String.Equals(Path.GetFileName(path), "user", StringComparison.OrdinalIgnoreCase);
        result.Add(new AzaharLocation { UserDirectory = path,
            Label = portable ? Path.GetFileName(Path.GetDirectoryName(path)) + " (portable)" : "Azahar (Windows user profile)" });
    }
    public static string RecentMario(string userDirectory) {
        string config = Path.Combine(userDirectory, "config", "qt-config.ini");
        if (!File.Exists(config)) return "";
        try {
            var files = Regex.Matches(File.ReadAllText(config), "\"([^\"\r\n]+\\.3ds)\"", RegexOptions.IgnoreCase)
                .Cast<Match>().Select(m => m.Groups[1].Value.Replace("\\\\", "\\"))
                .Where(p => File.Exists(p) && Regex.IsMatch(Path.GetFileName(p), "Mario.*3D.*Land", RegexOptions.IgnoreCase))
                .OrderByDescending(p => p.IndexOf("USA", StringComparison.OrdinalIgnoreCase) >= 0);
            return files.FirstOrDefault() ?? "";
        } catch { return ""; }
    }
    // Windows command-line quoting; arguments are passed directly to powershell -File.
    public static string Quote(string value) {
        return "\"" + Regex.Replace(value, "(\\\\*)\"", "$1$1\\\"").TrimEnd('\\') +
            new string('\\', value.Length - value.TrimEnd('\\').Length) +
            new string('\\', value.Length - value.TrimEnd('\\').Length) + "\"";
    }
    public static Tuple<int,string> RunBackend(string folder, string mode, string rom, string user) {
        var command = new List<string> { "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
            Path.Combine(folder, "Install-Patch.ps1"), "-Mode", mode };
        if (!String.IsNullOrEmpty(rom)) { command.Add("-RomPath"); command.Add(rom); }
        if (!String.IsNullOrEmpty(user)) { command.Add("-AzaharUserDirectory"); command.Add(user); }
        var info = new ProcessStartInfo {
            FileName = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "WindowsPowerShell", "v1.0", "powershell.exe"),
            Arguments = String.Join(" ", command.Select(Quote)), UseShellExecute = false,
            CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden,
            RedirectStandardOutput = true, RedirectStandardError = true, WorkingDirectory = folder
        };
        using (var process = Process.Start(info)) {
            var output = process.StandardOutput.ReadToEndAsync();
            var error = process.StandardError.ReadToEndAsync();
            process.WaitForExit();
            return Tuple.Create(process.ExitCode, output.Result + Environment.NewLine + error.Result);
        }
    }
}

internal sealed class SetupForm : Form {
    private readonly string package;
    private readonly TextBox rom = new TextBox();
    private readonly ComboBox locations = new ComboBox();
    private readonly Label locationPath = new Label();
    private readonly Label status = new Label();
    private readonly Button install = new Button();
    private readonly Button undo = new Button();
    private readonly Button browseRom = new Button();
    private readonly Button browseAzahar = new Button();
    private readonly ProgressBar progress = new ProgressBar();
    private readonly TextBox details = new TextBox();
    private readonly LinkLabel detailsLink = new LinkLabel();
    private readonly LinkLabel chooseData = new LinkLabel();
    private readonly List<AzaharLocation> detected;
    private bool busy;
    private bool showDetails;
    private bool renderingPreview;
    protected override bool ShowWithoutActivation { get { return renderingPreview; } }
    public SetupForm(string folder) {
        package = folder;
        Text = "Mario 60 FPS Setup";
        Font = new Font("Segoe UI", 10F);
        BackColor = Color.FromArgb(247, 249, 252);
        ForeColor = Color.FromArgb(26, 36, 51);
        ClientSize = new Size(730, 510);
        AutoScaleMode = AutoScaleMode.Dpi;
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        var title = LabelAt("Mario 3D Land · 60 FPS", 28, 24, 670, 42);
        title.Font = new Font("Segoe UI Semibold", 22F);
        LabelAt("Choose your game and Azahar, then install.", 30, 76, 660, 28);
        LabelAt("1   Your game", 30, 126, 600, 26).Font = new Font(Font, FontStyle.Bold);
        rom.SetBounds(32, 164, 542, 31);
        rom.ReadOnly = true; rom.BackColor = Color.White; rom.AccessibleName = "Super Mario 3D Land ROM file";
        Controls.Add(rom);
        MakeButton(browseRom, "Browse...", 586, 162, 112, 34);
        browseRom.AccessibleName = "Choose the Mario ROM file";
        browseRom.Click += delegate {
            using (var picker = new OpenFileDialog { Title = "Choose Super Mario 3D Land (USA Rev 1)", Filter = "Nintendo 3DS ROM (*.3ds)|*.3ds", CheckFileExists = true }) {
                if (File.Exists(rom.Text)) picker.FileName = rom.Text;
                if (picker.ShowDialog(this) == DialogResult.OK) { rom.Text = picker.FileName; UpdateState(); }
            }
        };
        LabelAt("Supports USA Rev 1. Your original game file stays unchanged.", 32, 202, 666, 26).ForeColor = Color.DimGray;
        LabelAt("2   Azahar", 30, 251, 600, 26).Font = new Font(Font, FontStyle.Bold);
        locations.SetBounds(32, 286, 542, 31); locations.DropDownStyle = ComboBoxStyle.DropDownList;
        Controls.Add(locations);
        MakeButton(browseAzahar, "Browse...", 586, 284, 112, 34);
        browseAzahar.AccessibleName = "Choose the Azahar program";
        browseAzahar.Click += delegate {
            using (var picker = new OpenFileDialog { Title = "Choose the Azahar program you use", Filter = "Azahar program (azahar.exe)|azahar.exe", CheckFileExists = true }) {
                if (picker.ShowDialog(this) != DialogResult.OK) return;
                string portable = Path.Combine(Path.GetDirectoryName(picker.FileName), "user");
                string selected = SetupPaths.IsUserDirectory(portable) ? portable :
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Azahar");
                if (SetupPaths.IsUserDirectory(selected)) AddLocation(selected);
                else MessageBox.Show(this, "Open Azahar once to create its data folder, then try again. You can also use 'Choose data folder' below.", "Azahar data folder", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        };
        locationPath.SetBounds(32, 326, 666, 32); locationPath.AutoEllipsis = true;
        locationPath.Font = new Font("Segoe UI", 8.5F); locationPath.ForeColor = Color.DimGray;
        Controls.Add(locationPath);
        chooseData.Text = "Choose data folder..."; chooseData.SetBounds(32, 363, 200, 24);
        chooseData.LinkClicked += delegate {
            using (var picker = new FolderBrowserDialog { Description = "Choose Azahar's data folder (contains config and sdmc or load)", ShowNewFolderButton = false }) {
                if (picker.ShowDialog(this) != DialogResult.OK) return;
                if (SetupPaths.IsUserDirectory(picker.SelectedPath)) AddLocation(picker.SelectedPath);
                else MessageBox.Show(this, "This folder does not look like Azahar's data folder. Choose the folder containing config and sdmc or load.", "Choose Azahar", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        };
        Controls.Add(chooseData);
        status.SetBounds(32, 405, 666, 40); status.Text = "Select a game to get started.";
        Controls.Add(status);
        progress.SetBounds(32, 447, 666, 4); progress.Style = ProgressBarStyle.Marquee; progress.Visible = false;
        Controls.Add(progress);
        MakeButton(install, "Install 60 FPS", 498, 463, 200, 35);
        install.BackColor = Color.FromArgb(30, 92, 218); install.ForeColor = Color.White;
        install.FlatStyle = FlatStyle.Flat; install.FlatAppearance.BorderSize = 0;
        MakeButton(undo, "Uninstall", 374, 463, 112, 35);
        detailsLink.Text = "Show details"; detailsLink.SetBounds(32, 471, 200, 24);
        detailsLink.LinkClicked += delegate {
            showDetails = !showDetails; details.Visible = showDetails;
            ClientSize = new Size(730, showDetails ? 664 : 510);
            detailsLink.Text = showDetails ? "Hide details" : "Show details";
        };
        Controls.Add(detailsLink);
        details.SetBounds(32, 522, 666, 120); details.Multiline = true; details.ScrollBars = ScrollBars.Vertical;
        details.ReadOnly = true; details.Visible = false; Controls.Add(details);
        install.Click += async delegate { await Apply("Install"); };
        undo.Click += async delegate { await Apply("Uninstall"); };
        FormClosing += delegate(object sender, FormClosingEventArgs e) { if (busy) e.Cancel = true; };
        detected = SetupPaths.Find(package);
        foreach (var item in detected) locations.Items.Add(item);
        locations.SelectedIndexChanged += delegate {
            var item = locations.SelectedItem as AzaharLocation;
            locationPath.Text = item == null ? "" : item.UserDirectory;
            if (String.IsNullOrEmpty(rom.Text) && item != null) rom.Text = SetupPaths.RecentMario(item.UserDirectory);
            UpdateState();
        };
        if (locations.Items.Count > 0) locations.SelectedIndex = 0;
        UpdateState();
    }
    private Label LabelAt(string text, int x, int y, int w, int h) {
        var label = new Label { Text = text, Left = x, Top = y, Width = w, Height = h };
        Controls.Add(label); return label;
    }
    private void MakeButton(Button button, string text, int x, int y, int w, int h) {
        button.Text = text; button.SetBounds(x, y, w, h); Controls.Add(button);
    }
    private void AddLocation(string path) {
        SetupPaths.Add(detected, path);
        locations.Items.Clear(); foreach (var item in detected) locations.Items.Add(item);
        for (int i = 0; i < locations.Items.Count; i++) {
            if (String.Equals(((AzaharLocation)locations.Items[i]).UserDirectory, Path.GetFullPath(path), StringComparison.OrdinalIgnoreCase)) { locations.SelectedIndex = i; break; }
        }
    }
    private void UpdateState() {
        if (busy) return;
        var item = locations.SelectedItem as AzaharLocation;
        bool managed = item != null && File.Exists(Path.Combine(item.UserDirectory, "load", "mods", "0004000000054000", "mario60-installation.json"));
        install.Enabled = !managed && item != null && File.Exists(rom.Text);
        install.Text = managed ? "Installed" : "Install 60 FPS";
        undo.Enabled = managed;
        status.ForeColor = Color.FromArgb(26, 36, 51);
        status.Text = managed ? "60 FPS patch installed. Open Azahar and play at 100% speed." :
            item == null ? "Use Browse beside Azahar to choose your emulator." :
            !File.Exists(rom.Text) ? "Choose your Super Mario 3D Land ROM." :
            "Ready to install. Existing patch files will be backed up.";
    }
    private async Task Apply(string mode) {
        var item = locations.SelectedItem as AzaharLocation;
        if (item == null) return;
        if (mode == "Uninstall" && MessageBox.Show(this, "Remove this patch and restore the previous files?", "Uninstall 60 FPS", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
        busy = true;
        install.Enabled = undo.Enabled = browseRom.Enabled = browseAzahar.Enabled = locations.Enabled = chooseData.Enabled = false;
        progress.Visible = true;
        status.Text = mode == "Install" ? "Checking your game and installing. Please wait..." : "Restoring previous files...";
        try {
            string game = rom.Text, user = item.UserDirectory;
            var result = await Task.Run(() => SetupPaths.RunBackend(package, mode, game, user));
            details.Text = result.Item2;
            if (result.Item1 != 0) {
                string error = result.Item2.Split(new [] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries).LastOrDefault(x => x.StartsWith("ERROR:")) ?? "Setup could not finish. See Show details.";
                MessageBox.Show(this, error.Replace("ERROR: ", ""), "Setup needs attention", MessageBoxButtons.OK, MessageBoxIcon.Information);
            } else MessageBox.Show(this, mode == "Install" ? "Installed! Open Azahar and start Mario normally. Keep speed at 100%." : "Patch removed. Previous files restored.", "Mario 60 FPS", MessageBoxButtons.OK, MessageBoxIcon.Information);
        } catch (Exception ex) { details.Text = ex.ToString(); MessageBox.Show(this, ex.Message, "Setup needs attention", MessageBoxButtons.OK, MessageBoxIcon.Information); }
        finally {
            busy = false; progress.Visible = false;
            browseRom.Enabled = browseAzahar.Enabled = locations.Enabled = chooseData.Enabled = true;
            UpdateState();
        }
    }
    public void SavePreview(string path) {
        renderingPreview = true; ShowInTaskbar = false; Opacity = 0;
        Show(); Application.DoEvents();
        using (var bitmap = new Bitmap(Width, Height)) { DrawToBitmap(bitmap, new Rectangle(0, 0, Width, Height)); bitmap.Save(path); }
        Hide();
    }
    public string SelectedUser { get { var item = locations.SelectedItem as AzaharLocation; return item == null ? "" : item.UserDirectory; } }
    public string SelectedRom { get { return rom.Text; } }
    public bool IsInstallReady { get { return install.Enabled; } }
}

internal static class Program {
    [STAThread]
    private static int Main(string[] args) {
        Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
        try {
            string folder = AppDomain.CurrentDomain.BaseDirectory;
            if (!File.Exists(Path.Combine(folder, "Install-Patch.ps1")) || !File.Exists(Path.Combine(folder, "code.ips")))
                throw new Exception("Extract the whole ZIP first. Keep this setup program with its other files.");
            using (var form = new SetupForm(folder)) {
                if (args.Length == 2 && args[0] == "--preview") {
                    form.SavePreview(args[1]);
                    File.WriteAllText(args[1] + ".txt", "Detected user: " + form.SelectedUser + "\r\nDetected ROM: " + form.SelectedRom + "\r\nInstall ready: " + form.IsInstallReady);
                    if (String.IsNullOrEmpty(form.SelectedUser) || String.IsNullOrEmpty(form.SelectedRom)) return 2;
                    var result = SetupPaths.RunBackend(folder, "Check", form.SelectedRom, form.SelectedUser);
                    File.AppendAllText(args[1] + ".txt", "\r\nBackend check: " + result.Item1 + "\r\n" + result.Item2);
                    return result.Item1;
                }
                Application.Run(form); return 0;
            }
        } catch (Exception ex) {
            if (args.Length > 0) File.WriteAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "setup-test-error.txt"), ex.ToString());
            else MessageBox.Show(ex.Message, "Mario 60 FPS Setup", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
