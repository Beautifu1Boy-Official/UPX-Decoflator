"""
UPX compress + strip signatures in one step.
If the file is already packed by UPX, skip compression and go straight to stripping.
Usage:
  python UPX-Decoflator.py <file> [file2] ...        process in-place
  python UPX-Decoflator.py -o <outpath> <file>        output to new file, keep original
"""
import sys
import subprocess
import os
import shutil

def upx_and_strip(filepath):
    if not os.path.isfile(filepath):
        print(f'  [-] File not found: {filepath}')
        return

    size_before = os.path.getsize(filepath)
    print(f'\n[*] Processing: {filepath} ({size_before/1024:.0f} KB)')

    # Step 1: UPX compress
    print(f'  [1] Running upx --best ...')
    result = subprocess.run(['upx', '--best', '--force', filepath],
                            capture_output=True, text=True)

    if result.returncode != 0:
        # Check if the error is because the file is already packed by UPX
        if "AlreadyPackedException" in result.stderr or "already packed by UPX" in result.stderr:
            print(f'  [i] File already packed by UPX, skipping compression')
        else:
            print(f'  [!] UPX failed: {result.stderr.strip()}')
            return
    else:
        size_after_upx = os.path.getsize(filepath)
        print(f'  [+] UPX done: {size_before/1024:.0f} KB -> {size_after_upx/1024:.0f} KB ({size_after_upx/size_before*100:.0f}%)')

    # Step 2: Strip signatures
    print(f'  [2] Stripping UPX signatures ...')
    data = bytearray(open(filepath, 'rb').read())
    patches = 0

    # Section names
    for old, new in {
        b'.UPX0\x00\x00\x00': b'.text\x00\x00\x00',
        b'.UPX1\x00\x00\x00': b'.rdata\x00\x00',
        b'.UPX2\x00\x00\x00': b'.rsrc\x00\x00\x00',
    }.items():
        while old in data:
            pos = data.find(old)
            data[pos:pos+8] = new
            patches += 1

    # UPX! magic
    while b'UPX!' in data:
        pos = data.find(b'UPX!')
        data[pos:pos+4] = b'\x00\x00\x00\x00'
        patches += 1

    # UPX0/1/2 strings
    for marker in [b'UPX0', b'UPX1', b'UPX2']:
        while marker in data:
            pos = data.find(marker)
            data[pos:pos+len(marker)] = b'\x00' * len(marker)
            patches += 1

    # Info string
    info = b'This file is packed with the UPX'
    pos = data.find(info)
    if pos != -1:
        start = pos
        while start > 0 and data[start-1] != 0:
            start -= 1
        end = pos + len(info)
        while end < len(data) and data[end] != 0:
            end += 1
        data[start:end] = b'\x00' * (end - start)
        patches += 1

    open(filepath, 'wb').write(data)
    print(f'  [+] {patches} signatures stripped')

    # Verify
    final = open(filepath, 'rb').read()
    clean = True
    for check in [b'UPX!', b'.UPX0', b'.UPX1', b'.UPX2']:
        if check in final:
            print(f'  [!] WARNING: {check} still found')
            clean = False
    if clean:
        print(f'  [+] Clean! No UPX signatures remain')

    print(f'  [+] Final size: {os.path.getsize(filepath)/1024:.0f} KB')

if __name__ == '__main__':
    args = sys.argv[1:]
    outpath = None

    if '-o' in args:
        idx = args.index('-o')
        if idx + 1 >= len(args):
            print(f'Usage: python {sys.argv[0]} -o <outpath> <file>')
            sys.exit(1)
        outpath = args[idx + 1]
        args.pop(idx)       # remove -o
        args.pop(idx)       # remove outpath value

    if len(args) < 1:
        print(f'Usage: python {sys.argv[0]} [-o <outpath>] <file> [file2] ...')
        sys.exit(1)

    if outpath and len(args) > 1:
        print('[-] -o only works with a single input file')
        sys.exit(1)

    if outpath:
        src = args[0]
        shutil.copy2(src, outpath)
        upx_and_strip(outpath)
    else:
        for f in args:
            upx_and_strip(f)

    print('\n[*] All done.')