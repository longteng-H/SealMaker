import struct, sys
sys.stdout.reconfigure(encoding='utf-8')
d = open(r'D:\rea_work\unpacked.exe', 'rb').read()
RSRC_VA = 0x338000; RSRC_RAW = 0x337400

def walk(base, path, depth=0, out=None):
    if out is None: out = []
    nn, nid = struct.unpack_from('<HH', d, base + 12)
    for i in range(nn + nid):
        o = base + 16 + i * 8
        name, offv = struct.unpack_from('<II', d, o)
        if name & 0x80000000:
            so = RSRC_RAW + (name & 0x7fffffff)
            ln, = struct.unpack_from('<H', d, so)
            nm = d[so + 2:so + 2 + ln * 2].decode('utf-16le', 'replace')
        else:
            nm = name
        if offv & 0x80000000:
            walk(RSRC_RAW + (offv & 0x7fffffff), path + [nm], depth + 1, out)
        else:
            e = RSRC_RAW + offv
            rva, size, cp, res = struct.unpack_from('<IIII', d, e)
            out.append((path + [nm], rva, size))
    return out

res = walk(RSRC_RAW, [])
forms = {p[1]: (rva, sz) for p, rva, sz in res if p[0] == 10}

class R:
    def __init__(self, b): self.b = b; self.p = 0
    def byte(self):
        v = self.b[self.p]; self.p += 1; return v
    def take(self, n):
        v = self.b[self.p:self.p + n]; self.p += n; return v
    def i32(self): v = struct.unpack('<i', self.take(4))[0]; return v
    def sstr(self):
        n = self.byte(); return self.take(n)
    def dec(self, b):
        for enc in ('utf-8', 'gbk'):
            try: return b.decode(enc)
            except Exception: pass
        return b.decode('latin1')

vaNull, vaList, vaInt8, vaInt16, vaInt32, vaExtended, vaString, vaIdent, vaFalse, vaTrue, vaBinary, vaSet, vaLString, vaNil, vaCollection, vaSingle, vaCurrency, vaDate, vaWString, vaInt64, vaUTF8String, vaDouble = range(22)

def read_value(r):
    t = r.byte()
    if t == vaNull: return None
    if t == vaList:
        out = []
        while True:
            if r.b[r.p] == vaNull: r.p += 1; break
            out.append(read_value(r))
        return out
    if t == vaInt8: return struct.unpack('<b', r.take(1))[0]
    if t == vaInt16: return struct.unpack('<h', r.take(2))[0]
    if t == vaInt32: return r.i32()
    if t == vaExtended: return struct.unpack('<d', r.take(10)[:8])[0]
    if t == vaString: return ('s', r.dec(r.sstr()))
    if t == vaIdent: return ('id', r.dec(r.sstr()))
    if t == vaFalse: return False
    if t == vaTrue: return True
    if t == vaNil: return None
    if t == vaBinary:
        n = r.i32(); return ('bin', n)
    if t == vaSet:
        out = []
        while True:
            s = r.sstr()
            if not s: break
            out.append(r.dec(s))
        return ('set', out)
    if t == vaLString:
        n = r.i32(); return ('s', r.dec(r.take(n)))
    if t == vaWString:
        n = r.i32(); return ('s', r.take(n * 2).decode('utf-16le', 'replace'))
    if t == vaUTF8String:
        n = r.i32(); return ('s', r.take(n).decode('utf-8', 'replace'))
    if t == vaCollection:
        items = []
        while True:
            b = r.byte()
            if b == 0: break
            if b == 0xF1:
                r.byte(); r.i32()
            props = {}
            while True:
                if r.b[r.p] == 0: r.p += 1; break
                pn = r.dec(r.sstr()); props[pn] = read_value(r)
            items.append(props)
        return ('coll', items)
    if t == vaSingle: return struct.unpack('<f', r.take(4))[0]
    if t == vaDouble: return struct.unpack('<d', r.take(8))[0]
    if t == vaCurrency: return struct.unpack('<q', r.take(8))[0] / 10000.0
    if t == vaDate: return struct.unpack('<d', r.take(8))[0]
    if t == vaInt64: return struct.unpack('<q', r.take(8))[0]
    raise ValueError(f'bad valuetype {t} at {r.p}')

KEEP = ('Caption', 'Text', 'Lines.Strings', 'Hint', 'Value', 'Min', 'Max', 'Checked', 'ItemIndex',
        'Font.Name', 'Font.Size', 'Font.Style', 'Align', 'Visible', 'TabVisible', 'Color',
        'Tag', 'Position', 'PageIndex', 'TabCaption', 'DisplayName')

def read_component(r, depth, out):
    b = r.byte()
    flags = 0; childpos = None
    if b == 0xF1:
        flags = r.byte(); childpos = r.i32()
    else:
        flags = b & 0xF0
        if (b & 0xF0) == 0xF0:
            return False
    if flags & 0x01:
        r.sstr()
    cls = r.dec(r.sstr())
    name = r.dec(r.sstr())
    props = {}
    while True:
        if r.b[r.p] == 0: r.p += 1; break
        pn = r.dec(r.sstr())
        try:
            v = read_value(r)
        except Exception as e:
            raise
        if pn in KEEP or any(k in pn for k in ('Caption', 'Text', 'Lines')):
            props[pn] = v
    desc = f'{"  " * depth}{cls} {name}'
    extra = []
    for k, v in props.items():
        if isinstance(v, tuple) and v[0] == 's' and v[1].strip():
            extra.append(f'{k}={v[1]!r}')
        elif isinstance(v, (int, float)) and k in ('Value', 'Min', 'Max', 'Checked', 'ItemIndex'):
            extra.append(f'{k}={v}')
    if extra: desc += '  | ' + ' '.join(extra)
    out.append(desc)
    if childpos is None:
        while True:
            if r.p >= len(r.b): break
            if not read_component(r, depth + 1, out): break
    else:
        pass
    return True

if __name__ == '__main__':
    tgt = sys.argv[1]
    rva, sz = forms[tgt]
    buf = d[RSRC_RAW + (rva - RSRC_VA):RSRC_RAW + (rva - RSRC_VA) + sz]
    assert buf[:4] == b'TPF0'
    r = R(buf); r.p = 4
    out = []
    while r.p < len(buf):
        if not read_component(r, 0, out): break
    print('\n'.join(out))
