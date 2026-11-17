import ctypes, ctypes.wintypes as wt, subprocess, time, os, sys, json
sys.stdout.reconfigure(encoding='utf-8')

k32 = ctypes.WinDLL('kernel32', use_last_error=True)

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000

class MBI32(ctypes.Structure):
    _fields_ = [('BaseAddress', wt.DWORD), ('AllocationBase', wt.DWORD),
                ('AllocationProtect', wt.DWORD), ('RegionSize', wt.DWORD),
                ('State', wt.DWORD), ('Protect', wt.DWORD), ('Type', wt.DWORD)]

k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.VirtualQueryEx.restype = ctypes.c_size_t
k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI32), ctypes.c_size_t]
k32.ReadProcessMemory.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

exe = r'D:\rea_work\stamp.exe'
p = subprocess.Popen([exe], cwd=os.path.dirname(exe))
time.sleep(3.0)
print('pid', p.pid, 'alive', p.poll() is None)

h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, p.pid)
print('handle', h)
if not h:
    print('open failed', ctypes.get_last_error()); sys.exit(1)

os.makedirs(r'D:\rea_work\dump', exist_ok=True)
manifest = []
addr = 0
buf = ctypes.create_string_buffer(0x1000)
nread = ctypes.c_size_t(0)
while addr < 0x80000000:
    mbi = MBI32()
    r = k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi))
    if not r or mbi.RegionSize == 0:
        addr += 0x1000
        continue
    size = mbi.RegionSize
    prot = mbi.Protect
    exe_flag = bool(prot & 0xF0)  # any EXECUTE
    rwx = (prot & 0xFF) in (0x40,)
    if mbi.State == MEM_COMMIT and size < 0x4000000 and (exe_flag or (0x10000 <= size < 0x800000)):
        data = bytearray()
        off = 0
        while off < size:
            chunk = min(0x10000, size - off)
            ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr + off), buf, 0x1000, ctypes.byref(nread)) if chunk >= 0x1000 else False
            if ok and nread.value:
                data += buf.raw[:nread.value]
                off += nread.value
            else:
                off += 0x1000
                if len(data) < off:
                    data += b'\x00' * (off - len(data))
        fn = f'dump_{addr:08x}_{size:08x}_p{prot:x}.bin'
        open(os.path.join(r'D:\rea_work\dump', fn), 'wb').write(bytes(data))
        manifest.append({'addr': hex(addr), 'size': size, 'protect': hex(prot), 'type': mbi.Type,
                         'file': fn, 'bytes': len(data),
                         'mz': bytes(data[:2]) == b'MZ', 'pe': bytes(data[:2]) == b'MZ' and b'PE\x00\x00' in bytes(data[:0x400])})
    addr += size

json.dump(manifest, open(r'D:\rea_work\dump\manifest.json', 'w'), indent=1)
for m in manifest:
    print(m)
p.terminate()
