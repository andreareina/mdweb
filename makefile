all: mdweb.py

mdweb.py: mdweb.mdweb
	mdweb --tangle program mdweb.mdweb > mdweb.py

install: mdweb.py
	echo '#!/usr/bin/env python' | cat - mdweb.py > mdweb
	chmod +x mdweb
	mv mdweb ~/bin/mdweb

clean:
	rm -f mdweb mdweb.py
