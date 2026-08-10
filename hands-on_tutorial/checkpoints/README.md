# Checkpoints

Each part within a session notebook writes a JSON manifest here after its declared artifacts have
been created. Consolidating the notebooks does not change checkpoint IDs or artifact handoffs.

```text
checkpoints/
├── session_01/part_1_1.json ... part_1_3.json
├── session_02/part_2_1.json ... part_2_5.json
└── session_03/part_3_1.json ... part_3_3.json
```

Generated manifests are ignored by Git. The `.gitkeep` files preserve the checkpoint directories in a fresh clone.

A manifest contains the part ID, completion time, artifact paths, existence checks, and a short summary. It records completion; it does not duplicate large data matrices.
