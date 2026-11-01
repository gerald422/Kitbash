import numpy as np
def read_stl(p):
    with open(p, 'rb') as f:
        f.read(80); n = np.frombuffer(f.read(4), np.uint32)[0]
        rec = np.frombuffer(f.read(n * 50), dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
    tri = rec["v"].reshape(-1, 3, 3).astype(float)
    V, inv = np.unique(tri.reshape(-1, 3).round(5), axis=0, return_inverse=True)
    T = inv.reshape(-1, 3)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for i in range(3): np.add.at(N, T[:, i], fn)
    N /= np.linalg.norm(N, axis=1)[:, None] + 1e-12
    return V, N, T
