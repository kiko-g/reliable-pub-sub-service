@echo off

if [%1]==[] (
  if [%2]==[] (
    set /A servers = 1
    set /A clients = 1
  )
)

if not [%1]==[] (
  if [%2]==[] (
    set /A servers = %1
    set /A clients = 1
  )
)

if not [%1]==[] (
  if not [%2]==[] (
    set /A servers = %1
    set /A clients = %2
  )
)

start python ../proxy.py

set i=0
:ServerLoop
start python ../server.py %i%
set /a i = %i% + 1
if not %i% == %servers% goto ServerLoop

set i=0
:ClientLoop
start python ../client.py %i%
set /a i = %i% + 1
if not %i% == %clients% goto ClientLoop

pause
