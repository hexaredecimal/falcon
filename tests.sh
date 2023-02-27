#!/usr/bin/bash

exp=$(ls tests/*.flc | wc -l)
line=$(cat tests/*.flc | wc -l)

printf "\033[91m%d\033[93m tests found\033[95m%s\033[0m\n" $exp
count=0
ls tests/*.flc | while read file 
do
    printf "\033[93mCompiling test: \033[95m%s\033[0m\n" $file
    ./falcon -c $file
done

printf "\033[92mDone compiling tests: \033[93m%s\033[0m\n" "Successfully"
printf "\033[91m%d\033[93m lines compiled\033[95m%s\033[0m\n" $line
