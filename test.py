import os
import fsspec

dataset1 = f"file://{os.environ['PIXI_PROJECT_ROOT']}/test/plain"
dataset2 = f"fszip://{os.environ['PIXI_PROJECT_ROOT']}/test/fszip"

fs1, root1 = fsspec.url_to_fs(dataset1)
fs2, root2 = fsspec.url_to_fs(dataset2)

# Check ls without detail (i.e. just file names)
list1 = sorted(i[len(root1) + 1 :] for i in fs1.ls(f"{root1}", detail=False))
list2 = sorted(i[len(root2) + 1 :] for i in fs2.ls(f"{root2}", detail=False))
assert list1 == list2

list1 = sorted(i[len(root1) + 1 :] for i in fs1.ls(f"{root1}/d", detail=False))
list2 = sorted(i[len(root2) + 1 :] for i in fs2.ls(f"{root2}/d", detail=False))
assert list1 == list2


# Check ls with detail:
#    - keep only "name" and "type" keys
#    - modify list2 paths to have the same as list1
#    - sort lists by "name" value
list1 = sorted(
    ({"name": d["name"], "type": d["type"]} for d in fs1.ls(f"{root1}", detail=True)),
    key=lambda d: d["name"],
)
list2 = sorted(
    (
        {"name": d["name"].replace("test/fszip", "test/plain"), "type": d["type"]}
        for d in fs2.ls(f"{root2}", detail=True)
    ),
    key=lambda d: d["name"],
)
assert list1 == list2

# Check reading files
for i in ("useful.txt", "useless.txt", "d/useful.txt", "d/useless.txt"):
    with fs1.open(f"{root1}/{i}") as f:
        content1 = f.read()
    with fs2.open(f"{root2}/{i}") as f:
        content2 = f.read()
    assert content1 == content2
