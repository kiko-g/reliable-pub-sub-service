#!/bin/bash
x=1
while [ $x -le $1 ]; do
  echo "Client Running"
  bash -c "python ../client.py $x true &"
  x=$(($x + 1))
done
