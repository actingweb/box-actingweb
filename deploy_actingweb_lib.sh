#!/bin/bash
#mv -v actingweb/config.py actingweb/config.pytmp
cp -vf ../acting-web-gae-library/actingweb/db/*.py actingweb/db/
cp -vf ../acting-web-gae-library/actingweb/*.py actingweb/
#mv -v actingweb/config.py actingweb/config_new.py
#mv -v actingweb/config.pytmp actingweb/config.py
cp -vf ../acting-web-gae-library/aw-*.py .
cp -vf ../acting-web-gae-library/*.yaml ./
cp -vf ../acting-web-gae-library/LICENSE ./
cp -vf ../acting-web-gae-library/README.txt ./
cp -vf ../acting-web-gae-library/CHANGELOG.txt ./CHANGELOG-aw.txt
echo Please review actingweb/config.py, index.yaml, and app.yaml for merge conflicts
echo Also review CHANGELOG-aw.txt from the actingweb library
