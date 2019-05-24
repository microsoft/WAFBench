OPENSSL=openssl-1.1.1b
SITE=https://www.openssl.org/source/

all:$(OPENSSL) 
	make buildopenssl

$(OPENSSL):
	wget $(SITE)/$(OPENSSL).tar.gz
	tar -xf $(OPENSSL).tar.gz

buildopenssl:
	cp Makefile_openssl $(OPENSSL)
	make -C $(OPENSSL) -f Makefile_openssl

clean:
	rm -rf openssl-*
