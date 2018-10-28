all: libapr wb 

libapr:
	make -C ./apr/ all
	

apr-skeleton: apr-skeleton.c 
	gcc apr-skeleton.c -o apr-skeleton -I./apr/aprutil-build/include/apr-1/ -I./apr/apr-build/include/apr-1/ -L./apr/apr-build/lib/ -static -lapr-1 -Wl,-Bdynamic -lpthread -lc -D_REENTRANT -D_GNU_SOURCE -D_LARGEFILE64_SOURCE


wb: wb.c ap_release.h
	gcc wb.c ap_release.h -g -o wb -I./apr/aprutil-build/include/apr-1/ -I./apr/apr-build/include/apr-1/ -L./apr/apr-build/lib/ -L./apr/aprutil-build/lib/ -Wl,-Bstatic -lapr-1 -laprutil-1 -Wl,-Bdynamic -lm -lc -lpthread -D_REENTRANT -D_GNU_SOURCE -D_LARGEFILE64_SOURCE -D_WAF_BENCH_ -DHAVE_OPENSSL -lssl -lcrypto

install: wb
	cp -f wb /usr/bin
	rm -rf /usr/bin/wb0
	ln -s /usr/bin/wb /usr/bin/wb0

clean:
	make -C ./apr/ clean
	rm -rf wb

