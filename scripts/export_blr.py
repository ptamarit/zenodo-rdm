"""Monthly dump of all BLR records in JSON for BiodiversityPMC (along with deleted records in CSV)."""

import gzip
import io
import json
from datetime import datetime

from flask import current_app
from invenio_app.factory import create_api
from invenio_search.proxies import current_search_client as client
from opensearch_dsl import Search
from xrootdpyfs import XRootDPyFS


def make_fs(klass):
    baseurl = f"root://eosuser.cern.ch//eos/project/z/zenodo/Dumps/{klass}/"

    return XRootDPyFS(baseurl)


app = create_api()


def dump_records(community_id):

    with app.app_context():
        idxprefix = current_app.config["SEARCH_INDEX_PREFIX"]

        # Dump the records
        t1 = datetime.now()
        print("Writing records ...")
        query = f"is_published:true AND is_deleted:true AND parent.communities.ids:{community_id}"
        s = (
            Search(using=client, index=f"{idxprefix}rdmrecords-records")
            .extra(
                track_total_hits=True,
            )
            .query(
                "query_string",
                query=query,
            )
        )

        # fs = make_fs("records-beta")
        stamp = datetime.now().date().isoformat()
        fp = None
        gzfile = None
        wrapper = None
        try:
            # fp = fs.open(f"records-{stamp}.jsonl.gz", 'wb')
            # gzfile = gzip.GzipFile(fileobj=fp, mode='wb')
            # wrapper = io.TextIOWrapper(gzfile, encoding='utf-8', newline='')
            i = 0
            for r in s.scan():
                # wrapper.write(json.dumps(r._d_))
                print(json.dumps(r._d_))
                i += 1
                if i % 1000 == 0:
                    print("...", i)
            print(f"... wrote {i} records")
        finally:
            if wrapper:
                wrapper.close()
            if gzfile:
                gzfile.close()
            if fp:
                fp.close()

        t2 = datetime.now()
        print("Writing records", t2 - t1)


# dump_records("c529f97d-f8cb-4c13-a439-9e36891694c2")  # Prod
dump_records("effe93b5-14de-4b1f-912d-d6673d75fb4d")  # Sandbox
