using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Web.Script.Serialization;

internal sealed class IniDocument {
    private readonly List<string> lines;
    public IniDocument(string text) { lines = text.Replace("\r\n", "\n").Split('\n').ToList(); }
    private int Find(string section, string key) {
        string current = "";
        for (int i = 0; i < lines.Count; i++) {
            string line = lines[i];
            if (line.StartsWith("[") && line.EndsWith("]")) current = line.Substring(1, line.Length - 2);
            else if (current == section && line.StartsWith(key + "=", StringComparison.Ordinal)) return i;
        }
        return -1;
    }
    public string Get(string section, string key) { int index = Find(section, key); return index < 0 ? null : lines[index].Substring(key.Length + 1); }
    public void Set(string section, string key, string value) {
        int index = Find(section, key);
        if (index >= 0) { if (value == null) lines.RemoveAt(index); else lines[index] = key + "=" + value; return; }
        if (value == null) return;
        int header = lines.FindIndex(x => x == "[" + section + "]");
        if (header < 0) { lines.Add("[" + section + "]"); lines.Add(key + "=" + value); return; }
        int end = header + 1;
        while (end < lines.Count && !lines[end].StartsWith("[")) end++;
        lines.Insert(end, key + "=" + value);
    }
    public override string ToString() { return String.Join("\r\n", lines); }
}
internal sealed class SettingChange {
    public string Path { get; set; }
    public string Section { get; set; }
    public string Key { get; set; }
    public string Before { get; set; }
    public string During { get; set; }
}
internal sealed class RecordSettings {
    private readonly string state;
    private readonly List<SettingChange> changes = new List<SettingChange>();
    public RecordSettings(string statePath) { state = statePath; }
    public static void Recover(string statePath) {
        if (!File.Exists(statePath)) return;
        var changes = new JavaScriptSerializer().Deserialize<List<SettingChange>>(File.ReadAllText(statePath));
        RestoreChanges(changes); File.Delete(statePath);
    }
    private void Add(string path, string section, string key, string value) {
        var doc = new IniDocument(File.ReadAllText(path));
        changes.Add(new SettingChange { Path = path, Section = section, Key = key, Before = doc.Get(section, key), During = value });
    }
    private void Setting(string path, string section, string key, string value) {
        Add(path, section, key, value); Add(path, section, key + "\\default", "false");
    }
    public void Apply(string user, string session, bool stereo = true) {
        if (File.Exists(state)) throw new InvalidOperationException("Recording settings from an earlier session still need recovery.");
        string global = Path.Combine(user, "config", "qt-config.ini");
        string custom = Path.Combine(user, "config", "custom", "0004000000054000.ini");
        File.Copy(global, Path.Combine(session, "qt-config.before.ini"));
        Setting(global, "UI", "singleWindowMode", "true");
        Setting(global, "UI", "fullscreen", "true");
        Setting(global, "UI", "displayTitleBars", "false");
        Setting(global, "UI", "showStatusBar", "false");
        Setting(global, "UI", "confirmClose", "false");
        Setting(global, "Layout", "layout_option", "1");
        Setting(global, "Layout", "render_3d", stereo ? "1" : "0");
        Setting(global, "Layout", "factor_3d", stereo ? "30" : "0");
        if (!stereo) Setting(global, "Layout", "mono_render_option", "0");
        Setting(global, "Layout", "swap_screen", "false");
        Setting(global, "Layout", "swap_eyes_3d", "false");
        Setting(global, "Layout", "upright_screen", "false");
        Setting(global, "Renderer", "resolution_factor", "9");
        Setting(global, "Renderer", "frame_limit", "100");
        Setting(global, "Renderer", "disable_right_eye_render", stereo ? "false" : "true");
        if (File.Exists(custom)) {
            File.Copy(custom, Path.Combine(session, "game-config.before.ini"));
            foreach (var change in changes.ToArray()) {
                if ((change.Section == "Layout" || change.Section == "Renderer") && !change.Key.Contains("\\"))
                    Add(custom, change.Section, change.Key + "\\use_global", "true");
            }
        }
        File.WriteAllText(state, new JavaScriptSerializer().Serialize(changes), new UTF8Encoding(false));
        foreach (var group in changes.GroupBy(x => x.Path)) {
            var doc = new IniDocument(File.ReadAllText(group.Key));
            foreach (var change in group) doc.Set(change.Section, change.Key, change.During);
            File.WriteAllText(group.Key, doc.ToString(), new UTF8Encoding(false));
        }
    }
    private static void RestoreChanges(List<SettingChange> changes) {
        foreach (var group in changes.GroupBy(x => x.Path)) {
            var doc = new IniDocument(File.ReadAllText(group.Key));
            foreach (var change in group) doc.Set(change.Section, change.Key, change.Before);
            File.WriteAllText(group.Key, doc.ToString(), new UTF8Encoding(false));
        }
    }
    public void Restore() { Recover(state); }
    public static void Test(string root, bool stereo = true) {
        string user = Path.Combine(root, "user"), config = Path.Combine(user, "config");
        Directory.CreateDirectory(Path.Combine(config, "custom"));
        string global = Path.Combine(config, "qt-config.ini");
        string original = "[Controls]\r\ncontroller=keep me\r\n[UI]\r\nfullscreen=false\r\n[Layout]\r\nrender_3d=2\r\n[Renderer]\r\nframe_limit=100\r\n";
        File.WriteAllText(global, original);
        string custom = Path.Combine(config, "custom", "0004000000054000.ini");
        File.WriteAllText(custom, "[Layout]\r\nrender_3d\\use_global=false\r\n");
        string session = Path.Combine(root, "session"); Directory.CreateDirectory(session);
        var settings = new RecordSettings(Path.Combine(root, "recovery.json")); settings.Apply(user, session, stereo);
        var during = new IniDocument(File.ReadAllText(global));
        if (during.Get("Layout", "layout_option") != "1" || during.Get("Layout", "render_3d") != (stereo ? "1" : "0") || during.Get("Layout", "factor_3d") != (stereo ? "30" : "0") || during.Get("Renderer", "disable_right_eye_render") != (stereo ? "false" : "true") || during.Get("Controls", "controller") != "keep me") throw new Exception("Recording settings check failed.");
        during.Set("Controls", "controller", "changed by user during session");
        File.WriteAllText(global, during.ToString()); settings.Restore();
        var after = new IniDocument(File.ReadAllText(global));
        if (after.Get("Layout", "render_3d") != "2" || after.Get("Layout", "layout_option") != null || after.Get("UI", "fullscreen") != "false" || after.Get("Controls", "controller") != "changed by user during session") throw new Exception("Recording settings restoration failed.");
        if (new IniDocument(File.ReadAllText(custom)).Get("Layout", "render_3d\\use_global") != "false") throw new Exception("Per-game settings restoration failed.");
        // Recovery after an interrupted session uses the same persisted journal.
        string session2 = Path.Combine(root, "session2"); Directory.CreateDirectory(session2);
        settings.Apply(user, session2, stereo); Recover(Path.Combine(root, "recovery.json"));
        if (new IniDocument(File.ReadAllText(global)).Get("Layout", "render_3d") != "2") throw new Exception("Interrupted recording recovery failed.");
    }
}
