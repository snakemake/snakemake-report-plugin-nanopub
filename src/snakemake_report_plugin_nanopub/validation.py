from nanopub import Nanopub
from rdflib import Namespace


def bind_nanopub_prefixes(np: Nanopub) -> Nanopub:
    """Bind canonical nanopub prefixes on the RDF dataset and return the nanopub.

    Binding is done before and after signing so serialization consistently
    exposes the nanopub URI namespace.
    """
    np_uri = str(np._metadata.np_uri)
    np.rdf.bind("this", Namespace(np_uri), replace=True)
    np.rdf.bind("sub", Namespace(np_uri + "/"), replace=True)
    return np
