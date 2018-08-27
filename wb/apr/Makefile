APR=apr-1.6.3
APRUTIL=apr-util-1.6.1
SITE=https://archive.apache.org/dist/apr

all:$(APR) $(APRUTIL) buildapr

$(APR):
	wget $(SITE)/$(APR).tar.gz
	tar -xf $(APR).tar.gz
$(APRUTIL):
	wget $(SITE)/$(APRUTIL).tar.gz
	tar -xf $(APRUTIL).tar.gz

buildapr:
	cp Makefile_apr $(APR)
	make -C $(APR) -f Makefile_apr
	cp Makefile_aprutil $(APRUTIL)
	make -C $(APRUTIL) -f Makefile_aprutil

clean:
	rm -rf apr-*
	rm -rf aprutil-*
