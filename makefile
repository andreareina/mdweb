all: mdweb.py

mdweb.py: mdweb.mdweb
	mdweb --tangle program mdweb.mdweb > mdweb.py

test: mdweb.py
	mdweb --tangle program mdweb.mdweb > /tmp/a
	python mdweb.py --tangle program mdweb.mdweb > /tmp/b
	diff -u /tmp/a /tmp/b

install: mdweb.py
	echo '#!/usr/bin/env python' | cat - mdweb.py > mdweb
	chmod +x mdweb
	mv mdweb ~/bin/mdweb

clean:
	rm -f mdweb mdweb.py
