PYTHON=`which python3`
# DESTDIR=/usr/bin/
BIN=$(DESTDIR)/usr/bin
PROJECT=squarepig

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"
	@echo "make test - Run tests"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --install-layout=deb --root $(DESTDIR) $(COMPILE)

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

builddeb:
	# pack man-page
	bzip2 -k man/squarepig.1
	# build the source package in the parent directory
	# then rename it to project_version.orig.tar.gz
	$(PYTHON) setup.py sdist --dist-dir=../
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*
	# build the package
	# dpkg-buildpackage -i.tox -i.git -I -rfakeroot
	debuild -S -sd

clean:
	$(PYTHON) setup.py clean
	rm -rf build/ MANIFEST
	find . -type f -name '*.pyc' -delete

inslocale:
	# build and install locales to system
	msgfmt -o locale/en_GB/LC_MESSAGES/squarepig.mo locale/en_GB/LC_MESSAGES/squarepig.po
	install -D locale/en_GB/LC_MESSAGES/squarepig.mo /usr/share/locale/en_GB/LC_MESSAGES/squarepig.mo
	msgfmt -o locale/de_DE/LC_MESSAGES/squarepig.mo locale/de_DE/LC_MESSAGES/squarepig.po
	install -D locale/de_DE/LC_MESSAGES/squarepig.mo /usr/share/locale/de_DE/LC_MESSAGES/squarepig.mo
