from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import str

import codecs
import json
import os, os.path
import re
from time import sleep
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import quote_plus, urlencode

import requests

def volume_metadata(id, marc=False):
    """
    Retrieve item metadata `from the HathiTrust Bibliographic API`_.

    Params:
    :param id: HTID for the volume to be retrieved
    :param marc: Retrieve MARC-XML within JSON return value.

    _ https://www.hathitrust.org/bib_api
    """
    biblio_api = "https://catalog.hathitrust.org/api/volumes"
    
    if marc:
        biblio_api += '/full'
    else:
        biblio_api += '/brief'

    url = biblio_api + '/htid/{}.json'.format(id)

    try:
        reader = codecs.getreader('utf-8')
        data = json.load(reader(urlopen(url)))
        if len(data['records']) == 1 and len(data['items']) == 1:
            md = data['records'].values()[0]
            md.update(data['items'][0])
        return md
    except (ValueError, IndexError, HTTPError):
        raise ValueError("No result found for " + id)


def safe_volume_metadata(id, marc=False):
    """
    Retrieve item metadata `from the HathiTrust Bibliographic API`_.
    
    Unlike :method volume_metadata:, this function returns an empty dictionary,
    rather than an error when metadata is missing.

    Params:
    :param id: HTID for the volume to be retrieved
    :param marc: Retrieve MARC-XML within JSON return value.

    _ https://www.hathitrust.org/bib_api
    """
    try:
        return volume_metadata
    except ValueError as err:
        logging.error(err)
        return dict()


def record_metadata(id, sleep_time=1):
    """
    Retrieve metadata for a HathiTrust Record.
    """
    regex = re.compile('\W')
    url = "http://catalog.hathitrust.org/api/volumes/brief/recordnumber/{0}.json"

    url = url.format(id)
    r = requests.get(url)
    data = r.json()

    # data = data['items'][id]
    items = []
    if data:
        for item in data['items']:
            enum = regex.sub('', str(item.get('enumcron', '')).lower())
            htid = item.get('htid', '')
            items.append((enum, htid))
    else:
        items = []

    sleep(sleep_time)
    return items



def volume_solr_metadata(id, sleep_time=0.1):
    """
    Retrieve metadata from HTRC Solr API.

    :method volume_metadata: returns much more up-to-date information. The HTRC
    Solr instance is used only for certain extracted features unavailable in the
    main HathiTrust Bibliographic API. If you are a recipient of a HTRC Advanced
    Collaborative Support (ACS) grant, then you may have to use this function.
    """
    solr = "http://chinkapin.pti.indiana.edu:9994/solr/meta/select/?q=id:%s" % id
    solr += "&wt=json"  # retrieve JSON results
    if sleep_time:
        sleep(sleep_time)  # JUST TO MAKE SURE WE ARE THROTTLED
    try:
        reader = codecs.getreader('utf-8')
        data = json.load(reader(urlopen(solr)))
        return data['response']['docs'][0]
    except (ValueError, IndexError, HTTPError):
        logging.error("No result found for " + id)
        return dict()


def folder_volume_metadata(folder, output_file=None):
    """
    Retrieves metadata for a folder of folders, where each subfolder is named
    for a HathiTrust ID. This structure is the default structure extracted from
    a Data API request (:method htrc.volumes.get_volumes:). 
    """
    ids = os.listdir(folder)
    data = [(id.strip(), volume_metadata(id.strip())) for id in ids
                if not id.endswith('.log')]
    data = dict(data)

    if output_file:
        with open(os.path.join(folder, '../metadata.json'), 'w') as outfile:
            json.dump(data, outfile)
    else:
        return data

