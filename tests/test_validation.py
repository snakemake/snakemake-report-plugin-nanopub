from types import SimpleNamespace

from snakemake_report_plugin_nanopub.validation import bind_nanopub_prefixes


class DummyRdf:
    def __init__(self):
        self.calls = []

    def bind(self, prefix, namespace, replace=False):
        self.calls.append((prefix, str(namespace), replace))


class DummyNanopub:
    def __init__(self, np_uri: str):
        self._metadata = SimpleNamespace(np_uri=np_uri)
        self.rdf = DummyRdf()


def test_bind_nanopub_prefixes_binds_this_and_sub_and_returns_same_object():
    np_obj = DummyNanopub("https://w3id.org/np/RAExample123")

    result = bind_nanopub_prefixes(np_obj)

    assert result is np_obj
    assert ("this", "https://w3id.org/np/RAExample123", True) in np_obj.rdf.calls
    assert ("sub", "https://w3id.org/np/RAExample123/", True) in np_obj.rdf.calls
