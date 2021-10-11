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


echo "export TVM_HOME=`pwd`/src/tvm" >> ~/.bashrc
echo "export AX_HOME=`pwd`/src/Ax" >> ~/.bashrc
echo "export PYTHONPATH=\$TVM_HOME/python:\$AX_HOME:\${PYTHONPATH}" >> ~/.bashrc

cd ..
sed -i "s#tenet_path = \"~/TENET/bin/HASCO_interface\"#tenet_path = \"`pwd`/TENET/bin/HASCO_interface\"#g" ./HASCO/src/codesign/config.py
sed -i "s#tensorlib_home = \"~/TensorLib/\"#tensorlib_home = \"`pwd`/TensorLib/\"#g" ./HASCO/src/codesign/config.py

echo "Finished"