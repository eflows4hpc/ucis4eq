#!/bin/bash

cp $1 $2


sed -i "s/STRIKE = 0/STRIKE = $3/g" $2
sed -i "s/RAKE = 180.00/RAKE = $4/g" $2
sed -i "s/DIP = 90/DIP = $5/g" $2
