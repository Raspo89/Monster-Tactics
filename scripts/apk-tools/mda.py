"""Minimal reader for the game's static .MDA meshes (weapons, shields, armour pieces).

Layout worked out from the files and checked against the monster models already converted:
  header: u32 version, u32 vertexCount|0x80000000, u32 positions, u32 normals, u32 uvs, u32 tangents, u32 groups, u32, u32
  positions f32x3, uvs i16x2 (/4096, v flipped), normals 4×i8 (z,y,x,_), tangents 4 bytes,
  per group: u32 0xffffffff, 16 bytes, ..., u16 vertexCount, u16 indexCount, indices u16,
  then one 12-byte record per vertex: u16 position, u16, u16, u16, u16 uv, u16 (column choice checked by rendering; normals are recomputed when drawing).
Only single-group, unskinned meshes are read (all equipment)."""
import struct
import numpy as np

def read(path, pc=0, uc=4, nc=4):
    d = open(path, 'rb').read()
    h = struct.unpack('<9I', d[:36])
    nv, npos, nn, nuv, nt, groups = h[1] & 0xffff, h[2], h[3], h[4], h[5], h[6]
    o = 36
    pos = np.frombuffer(d[o:o + npos * 12], '<f4').reshape(-1, 3); o += npos * 12
    uv = np.frombuffer(d[o:o + nuv * 4], '<i2').reshape(-1, 2) / 4096.0; o += nuv * 4
    nb = np.frombuffer(d[o:o + nn * 4], '<i1').reshape(-1, 4)[:, [2, 1, 0]].astype(float); o += nn * 4
    nrm = nb / np.maximum(np.linalg.norm(nb, axis=1, keepdims=True), 1e-6)
    o += nt * 4
    parts = []; done = 0
    while done < nv:
        # each sub-mesh starts after a short header (marker / bounds); find "04 00, name length, name"
        for k in range(o, o + 48):
            if d[k:k + 2] != b'\x04\x00': continue
            L = d[k + 2]; name = d[k + 3:k + 3 + L]
            if all(32 <= c < 127 for c in name):
                v, ni = struct.unpack('<HH', d[k + 3 + L:k + 7 + L])
                if 0 < v <= nv - done and ni and ni % 3 == 0: break
        else: raise ValueError('no sub-mesh header in ' + path)
        name = name.decode('latin1'); o = k + 3 + L
        v, ni = struct.unpack('<HH', d[o:o + 4]); o += 4
        idx = np.frombuffer(d[o:o + ni * 2], '<u2').astype(int); o += ni * 2
        rec = np.frombuffer(d[o:o + v * 12], '<u2').reshape(-1, 6); o += v * 12
        T = idx.reshape(-1, 3)
        def uv_edge(c):
            if rec[:, c].max() >= nuv or rec[:, c].max() == 0: return 9e9
            X = uv[rec[:, c]][T]; return np.linalg.norm(X[:, 0] - X[:, 1], axis=1).mean()
        uc = min(range(rec.shape[1]), key=lambda c: (c != 4, 0)) if uv_edge(4) < 9e9 else min(range(rec.shape[1]), key=uv_edge)
        if not len(idx) or idx.max() >= v or rec[:, pc].max() >= npos or uv_edge(uc) >= 9e9:
            raise ValueError('bad sub-mesh in ' + path)
        U = uv[rec[:, uc]].copy(); U[:, 1] = 1 - U[:, 1]
        parts.append({'texture': name, 'positions': pos[rec[:, pc]], 'uv': U, 'normals': nrm[np.minimum(rec[:, nc], nn - 1)], 'indices': idx})
        done += v
    return parts
