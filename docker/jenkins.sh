#!/bin/bash

echo "************ RUNNING TESTS *************"

# test
docker run \
  -v /var/lib/jenkins/workspace/GeoMop:/mnt/GeoMop \
  -v /root/.ssh:/root/.ssh \
  geomop/test \
  /home/geomop/test.sh
if [[ $? != 0 ]]; then exit 1; fi

echo "************ RUNNING BUILD *************"

# build
docker run \
  -v /var/lib/jenkins/workspace/GeoMop:/mnt/GeoMop \
  -e VERSION=$VERSION \
  geomop/build \
  bin/bash -c " \
    /home/geomop/build.sh; \
    chown -R $(id -u):$(id -g) /mnt/GeoMop \
  "
if [[ $? != 0 ]]; then exit 1; fi

echo "************** SUCCESS ****************"

exit 0
