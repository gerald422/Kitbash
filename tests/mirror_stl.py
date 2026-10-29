import sys, numpy as np
def mirror(src, dst):
    with open(src, 'rb') as f:
        head = f.read(80); n = np.frombuffer(f.read(4), np.uint32)[0]
        rec = np.frombuffer(f.read(n * 50), dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]).copy()
    v = rec["v"].reshape(-1, 3, 3); v[:, :, 0] *= -1; rec["v"] = v[:, ::-1, :].reshape(-1, 9)
    rec["n"][:, 0] *= -1
    with open(dst, 'wb') as f:
        f.write(head); f.write(np.uint32(n).tobytes()); f.write(rec.tobytes())
if __name__ == '__main__':
    mirror(sys.argv[1], sys.argv[2])
