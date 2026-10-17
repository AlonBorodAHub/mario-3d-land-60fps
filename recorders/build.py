from pathlib import Path
import os,subprocess
p=Path(__file__).resolve().parent
csc=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
for mono,name in [(False,'Record Mario in Azahar.exe'),(True,'Record Mario 2D in Azahar.exe')]:
    subprocess.run([str(csc),'/nologo','/target:winexe','/optimize+']+(['/define:MONO'] if mono else [])+[
      '/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/reference:System.Core.dll','/reference:System.Web.Extensions.dll',
      '/win32manifest:'+str(p/'setup.manifest'),'/out:'+str(p.parent/name)]+[str(p/n) for n in ['MarioRecorder.cs','RecordSettings.cs','LoopbackCapture.cs','PortableConfiguration.cs']],check=True)
