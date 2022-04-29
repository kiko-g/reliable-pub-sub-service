#!/bin/bash

x=1

while [ $x -le $1 ]; do
  x-terminal-emulator -e python ../src/server.py
  x=$(($x + 1))
done

x=1

while [ $x -le $2 ]; do
  x-terminal-emulator -e python ../src/client.py $x true
  x=$(($x + 1))
done

python ../src/proxy.py
