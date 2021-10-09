#!./bin/bash

echo "Building tvm"
cd ./src/tvm
mkdir build
sed "s/set(USE_LLVM OFF)/set(USE_LLVM llvm-config-9)/g" cmake/config.cmake > build/config.cmake
cd build
cmake ..
make -j8
cd ../..

echo "Building Maestro"
cd maestro
scons
cd ..

echo "Building Ax"
cd Ax
sudo python3 setup.py install
cd ../..

echo "Post configure"
mkdir -p rst/mapping
mkdir -p rst/config
mkdir -p rst/software

echo "Finished"