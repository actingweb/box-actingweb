#!/bin/bash
cp -vf ../acting-web-gae-library-dev/actingweb/db/*.py actingweb/db/
cp -vf ../acting-web-gae-library-dev/actingweb/*.py actingweb/
cp -vf ../acting-web-gae-library-dev/aw-*.py .
cp -vf ../acting-web-gae-library-dev/*.yaml ./
cp -vf ../acting-web-gae-library-dev/LICENSE ./
cp -vf ../acting-web-gae-library-dev/README.txt ./
cp -vf ../acting-web-gae-library-dev/CHANGELOG.txt ./CHANGELOG-aw.txt
echo Please review actingweb/config.py, index.yaml, and app.yaml for merge conflicts
echo Also review CHANGELOG-aw.txt from the actingweb library
