// Used by the GitHub distribution; local project launchers keep their existing setup.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;
using System.Windows.Forms;

internal sealed class PortableConfiguration {
    public string Emulator { get; set; }
    public string Rom { get; set; }
    public string UserDirectory { get; set; }
    private static bool IsUser(string folder) {
        return !String.IsNullOrEmpty(folder) && Directory.Exists(Path.Combine(folder, "config")) &&
            (Directory.Exists(Path.Combine(folder, "sdmc")) || Directory.Exists(Path.Combine(folder, "load")));
    }
    private static string PickFile(string title, string filter) {
        using (var dialog = new OpenFileDialog { Title = title, Filter = filter, CheckFileExists = true }) {
            if (dialog.ShowDialog() != DialogResult.OK) throw new OperationCanceledException("Recording setup cancelled.");
            return dialog.FileName;
        }
    }
    public static PortableConfiguration Load(string root) {
        string file = Path.Combine(root, "recording-config.json");
        var json = new JavaScriptSerializer();
        var result = File.Exists(file) ? json.Deserialize<PortableConfiguration>(File.ReadAllText(file)) : new PortableConfiguration();
        if (!File.Exists(result.Emulator)) {
            var ancestor = new DirectoryInfo(root);
            for (int depth = 0; ancestor != null && depth < 5 && !File.Exists(result.Emulator); depth++, ancestor = ancestor.Parent) {
                foreach (var relative in new [] { "Azahar-validation", "Azahar", "." }) {
                    string candidate = Path.Combine(ancestor.FullName, relative, "azahar.exe");
                    if (File.Exists(candidate)) { result.Emulator = candidate; break; }
                }
            }
            if (!File.Exists(result.Emulator)) result.Emulator = PickFile("Choose the Azahar program you use", "Azahar (azahar.exe)|azahar.exe");
        }
        if (!IsUser(result.UserDirectory)) {
            string portable = Path.Combine(Path.GetDirectoryName(result.Emulator), "user");
            string roaming = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Azahar");
            if (IsUser(portable)) result.UserDirectory = portable;
            else if (IsUser(roaming)) result.UserDirectory = roaming;
            else using (var dialog = new FolderBrowserDialog { Description = "Choose Azahar's data folder (contains config and sdmc or load)", ShowNewFolderButton = false }) {
                if (dialog.ShowDialog() != DialogResult.OK) throw new OperationCanceledException("Recording setup cancelled.");
                result.UserDirectory = dialog.SelectedPath;
            }
            if (!IsUser(result.UserDirectory)) throw new IOException("The selected Azahar data folder is not valid. Open Azahar once to create its profile.");
        }
        if (!File.Exists(result.Rom)) {
            string config = Path.Combine(result.UserDirectory, "config", "qt-config.ini");
            if (File.Exists(config)) {
                result.Rom = Regex.Matches(File.ReadAllText(config), "\"([^\"\r\n]+\\.3ds)\"", RegexOptions.IgnoreCase)
                    .Cast<Match>().Select(m => m.Groups[1].Value.Replace("\\\\", "\\"))
                    .Where(p => File.Exists(p) && Regex.IsMatch(Path.GetFileName(p), "Mario.*3D.*Land", RegexOptions.IgnoreCase))
                    .OrderByDescending(p => p.IndexOf("USA", StringComparison.OrdinalIgnoreCase) >= 0).FirstOrDefault();
            }
            if (!File.Exists(result.Rom)) result.Rom = PickFile("Choose Super Mario 3D Land (USA Rev 1)", "3DS ROM (*.3ds)|*.3ds");
        }
        File.WriteAllText(file, json.Serialize(result), new UTF8Encoding(false));
        return result;
    }
}
