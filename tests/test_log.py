from ftw_compatible_tool import log
from ftw_compatible_tool import broker
from ftw_compatible_tool import context
from ftw_compatible_tool import traffic


_TEST_MODSECURITY_LOG = '''
2019/04/11 19:20:46 [error] 392#392: [client 172.17.0.1] ModSecurity: collection_store_ex_origin: Failed to access DBM file "/var/log/modsecurity//ip": No such file or directory [hostname
"0a9de2faed93"] [uri "/AppScan_fingerprint/MAC_ADDRESS_01234567890.html"] [unique_id "AFAcUcOOAcAcAcXcAcwcAcAc"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#412: [client 172.17.0.1] ModSecurity: Access denied with code 403 (phase 1). Pattern match "magic-(\\w*)" at REQUEST_HEADERS:Host. [file "/root/src/owasp-modsecurity-crs-3.1.0/modsecurity_init.conf"] [line "8"] [id "010203"] [msg "delimiter-magic-284006541951478418388062796500664128516"] [hostname "0a9de2faed93"] [uri "/"] [unique_id "AcAcAcAcAcAcAcAcAcAcCcAc"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#413: [client 172.17.0.1] ModSecurity: Access denied with code 403 (phase 1). Pattern match "magic-(\\w*)" at REQUEST_HEADERS:Host. [file "/root/src/owasp-modsecurity-crs-3.1.0/modsecurity_init.conf"] [line "8"] [id "010203"] [msg "delimiter-magic-284026009895571423421096282120140690436"] [hostname "0a9de2faed93"] [uri "/"] [unique_id "A8UcAcscMcAcAcAcAcAlAcAA"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#414: [client 172.17.0.1] ModSecurity: Warning. Matched phrase "/nessus_is_probing_you_" at REQUEST_FILENAME. [file "/root/src/owasp-modsecurity-crs-3.1.0/rules/REQUEST-913-SCANNER-DETECTION.conf"] [line "108"] [id "913120"] [msg "Found request filename/argument associated with security scanner"] [data "Matched Data: /nessus_is_probing_you_ found within REQUEST_FILENAME: /nessus_is_probing_you_"] [severity "CRITICAL"] [ver "OWASP_CRS/3.1.0"] [tag "application-multi"] [tag "language-multi"] [tag "platform-multi"] [tag "attack-reputation-scanner"] [tag "OWASP_CRS/AUTOMATION/SECURITY_SCANNER"] [tag "WASCTC/WASC-21"] [tag "OWASP_TOP_10/A7"] [tag "PCI/6.5.10"] [hostname "0a9de2faed93"] [uri "/nessus_is_probing_you_"] [unique_id "AnAcucAcacUOAUhcAcAcM5zc"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#414: [client 172.17.0.1] ModSecurity: Warning. Operator EQ matched 0 at REQUEST_HEADERS. [file "/root/src/owasp-modsecurity-crs-3.1.0/rules/REQUEST-920-PROTOCOL-ENFORCEMENT.conf"] [line "1335"] [id "920320"] [msg "Missing User Agent Header"] [severity "NOTICE"] [ver "OWASP_CRS/3.1.0"] [tag "application-multi"] [tag "language-multi"] [tag "platform-multi"] [tag "attack-protocol"] [tag "OWASP_CRS/PROTOCOL_VIOLATION/MISSING_HEADER_UA"] [tag "WASCTC/WASC-21"] [tag "OWASP_TOP_10/A7"] [tag "PCI/6.5.10"] [tag "paranoia-level/2"] [hostname "0a9de2faed93"] [uri "/nessus_is_probing_you_"] [unique_id "AnAcucAcacUOAUhcAcAcM5zc"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#414: [client 172.17.0.1] ModSecurity: Access denied with code 403 (phase 2). Operator GE matched 5 at TX:anomaly_score. [file "/root/src/owasp-modsecurity-crs-3.1.0/rules/REQUEST-949-BLOCKING-EVALUATION.conf"] [line "93"] [id "949110"] [msg "Inbound Anomaly Score Exceeded (Total Score: 7)"] [severity "CRITICAL"] [tag "application-multi"] [tag "language-multi"] [tag "platform-multi"] [tag "attack-generic"] [hostname "0a9de2faed93"] [uri "/nessus_is_probing_you_"] [unique_id "AnAcucAcacUOAUhcAcAcM5zc"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#392: [client 172.17.0.1] ModSecurity: Warning. Operator GE matched 5 at TX:inbound_anomaly_score. [file "/root/src/owasp-modsecurity-crs-3.1.0/rules/RESPONSE-980-CORRELATION.conf"] [line "86"] [id "980130"] [msg "Inbound Anomaly Score Exceeded (Total Inbound Score: 7 - SQLI=0,XSS=0,RFI=0,LFI=0,RCE=0,PHPI=0,HTTP=0,SESS=0): Missing User Agent Header; individual paranoia level scores: 5, 2, 0, 0"] [tag "event-correlation"] [hostname "0a9de2faed93"] [uri "/nessus_is_probing_you_"] [unique_id "AnAcucAcacUOAUhcAcAcM5zc"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#392: [client 172.17.0.1] ModSecurity: collection_store_ex_origin: Failed to access DBM file "/var/log/modsecurity//ip": No such file or directory [hostname
"0a9de2faed93"] [uri "/nessus_is_probing_you_"] [unique_id "AnAcucAcacUOAUhcAcAcM5zc"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#415: [client 172.17.0.1] ModSecurity: Access denied with code 403 (phase 1). Pattern match "magic-(\\w*)" at REQUEST_HEADERS:Host. [file "/root/src/owasp-modsecurity-crs-3.1.0/modsecurity_init.conf"] [line "8"] [id "010203"] [msg "delimiter-magic-284026009895571423421096282120140690436"] [hostname "0a9de2faed93"] [uri "/"] [unique_id "AcPcAUANAcQcAcAcAcmcAtAc"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#416: [client 172.17.0.1] ModSecurity: Access denied with code 403 (phase 1). Pattern match "magic-(\\w*)" at REQUEST_HEADERS:Host. [file "/root/src/owasp-modsecurity-crs-3.1.0/modsecurity_init.conf"] [line "8"] [id "010203"] [msg "delimiter-magic-282099401237516304385679803300151104516"] [hostname "0a9de2faed93"] [uri "/"] [unique_id "AcAcAcAc3cscXcAiAcAcAcAc"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#417: [client 172.17.0.1] ModSecurity: Warning. Match of "pm AppleWebKit Android" against "REQUEST_HEADERS:User-Agent" required. [file "/root/src/owasp-modsecurity-crs-3.1.0/rules/REQUEST-920-PROTOCOL-ENFORCEMENT.conf"] [line "1276"] [id "920300"] [msg "Request Missing an Accept Header"] [severity "NOTICE"] [ver "OWASP_CRS/3.1.0"] [tag "application-multi"] [tag "language-multi"] [tag "platform-multi"] [tag "attack-protocol"] [tag "OWASP_CRS/PROTOCOL_VIOLATION/MISSING_HEADER_ACCEPT"] [tag "WASCTC/WASC-21"] [tag "OWASP_TOP_10/A7"] [tag "PCI/6.5.10"] [tag "paranoia-level/2"] [hostname "0a9de2faed93"] [uri "/"] [unique_id "AcAp75AcAlAYAcAcAcXcAcAh"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#418: [client 172.17.0.1] ModSecurity: Warning. Match of "pm AppleWebKit Android" against "REQUEST_HEADERS:User-Agent" required. [file "/root/src/owasp-modsecurity-crs-3.1.0/rules/REQUEST-920-PROTOCOL-ENFORCEMENT.conf"] [line "1276"] [id "920300"] [msg "Request Missing an Accept Header"] [severity "NOTICE"] [ver "OWASP_CRS/3.1.0"] [tag "application-multi"] [tag "language-multi"] [tag "platform-multi"] [tag "attack-protocol"] [tag "OWASP_CRS/PROTOCOL_VIOLATION/MISSING_HEADER_ACCEPT"] [tag "WASCTC/WASC-21"] [tag "OWASP_TOP_10/A7"] [tag "PCI/6.5.10"] [tag "paranoia-level/2"] [hostname "0a9de2faed93"] [uri "/index.html"] [unique_id "AcAcAcpcAcAcAcAcAcANA6Ac"] [requestheaderhostname "0a9de2faed93"]
2019/04/11 19:20:46 [error] 392#419: [client 172.17.0.1] ModSecurity: Access denied with code 403 (phase 1). Pattern match "magic-(\\w*)" at REQUEST_HEADERS:Host. [file "/root/src/owasp-modsecurity-crs-3.1.0/modsecurity_init.conf"] [line "8"] [id "010203"] [msg "delimiter-magic-282099401237516304385679803300151104516"] [hostname "0a9de2faed93"] [uri "/"] [unique_id "ncAcYcAnAkAc4cAWAcAcACAc"] [requestheaderhostname "0a9de2faed93"]
'''


def test_log_extract():
    counter = {
        "log" : 0,
    }
    def get_log(*args):
        counter["log"] += 1
    ctx = context.Context(broker.Broker(), traffic.Delimiter("magic"))
    ctx.broker.subscribe(broker.TOPICS.SQL_COMMAND, get_log)
    collector = log.LogCollector(ctx)
    for line in _TEST_MODSECURITY_LOG.splitlines():
        ctx.broker.publish(broker.TOPICS.RAW_LOG, line + "\n")
    assert(counter["log"] == 2)


