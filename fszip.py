import fsspec
from fsspec.spec import AbstractFileSystem
from pathlib import Path


class ZipAwareFileSystem(AbstractFileSystem):
    protocol = "fszip"
    root_marker = "/"

    @property
    def filesystem(self):
        if getattr(self, "_filesystem", None) is None:
            self._filesystem = fsspec.filesystem("file")
        return self._filesystem

    def _resolve(self, path):
        path = Path(path)
        parent = path.parent
        zip = None
        zip_path = None
        while True:
            if not parent.name:
                break
            zip = parent / "_fs.zip"
            if zip.exists():
                zip_path = path.relative_to(parent)
                break
            zip = None
            parent = parent.parent
        if zip:
            return (fsspec.filesystem("zip", fo=str(zip), mode="r"), str(zip_path))
        return (None, None)

    def info(self, path, **kwargs):
        fs, path = self._resolve(path)
        return fs.info(path, **kwargs)

    def ls(self, path, detail=True, **kwargs):
        zip, zip_path = self._resolve(path)
        unfiltered_result = self.filesystem.ls(path, detail=detail, **kwargs)
        if detail:
            result = {}
            for d in unfiltered_result:
                if d["name"].endswith("/_fs.zip"):
                    if not zip:
                        zip = fsspec.filesystem("zip", fo=d["name"], mode="r")
                        zip_path = "/"
                else:
                    result[d["name"]] = d
            if zip:
                if zip_path == "/":
                    path_limit = None
                else:
                    path_limit = -len(zip_path) - 1
                for i in zip.ls(zip_path, detail=detail, **kwargs):
                    i["name"] = f'{path[:path_limit]}/{i["name"]}'
                    result[i["name"]] = i
            return list(result.values())
        else:
            result = set()
            for d in unfiltered_result:
                if d.endswith("/_fs.zip"):
                    if not zip:
                        zip = fsspec.filesystem("zip", fo=d, mode="r")
                        zip_path = "/"
                else:
                    result.add(d)
            if zip:
                if zip_path == "/":
                    path_limit = None
                else:
                    path_limit = -len(zip_path) - 1
                result.update(
                    f"{path[:path_limit]}/{i}"
                    for i in zip.ls(zip_path, detail=detail, **kwargs)
                )
            return list(result)

    def _open(self, path, **kwargs):
        path = Path(path)
        if path.exists():
            return self.filesystem.open(path, **kwargs)
        zip, zip_path = self._resolve(path)
        result = zip._open(zip_path, **kwargs)
        # Keep the filesystem alive as long as the opened file is existing.
        #
        result._zip = zip
        return result
