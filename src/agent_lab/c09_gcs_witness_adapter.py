"""Bounded GCS witness adapter. Not wired into protected Kernel operations.

Caller supplies independent credentials and MAC key; never logs them.
"""
from __future__ import annotations

from urllib.parse import quote

import requests
from .c09_witness_protocol import WitnessError, WitnessRecord


class GCSWitnessAdapter:
    def __init__(self, bucket: str, writer_token_provider, reader_token_provider, session=None):
        if not bucket or '/' in bucket:
            raise ValueError('invalid bucket')
        self.bucket = bucket
        self.writer_token_provider = writer_token_provider
        self.reader_token_provider = reader_token_provider
        self.session = session or requests.Session()

    def _request(self, method: str, path: str, *, reader=False, **kwargs):
        token = (self.reader_token_provider if reader else self.writer_token_provider)()
        if not token:
            raise WitnessError('witness credentials unavailable')
        headers = {'Authorization': 'Bearer ' + token}
        headers.update(kwargs.pop('headers', {}))
        try:
            response = self.session.request(method, path, headers=headers, timeout=20, **kwargs)
        except requests.RequestException as exc:
            raise WitnessError('witness provider unavailable') from exc
        return response

    def append(self, record: WitnessRecord, mac_key: bytes):
        record.verify(mac_key)
        payload = record.to_bytes()
        endpoint = 'https://storage.googleapis.com/upload/storage/v1/b/' + quote(self.bucket, safe='') + '/o'
        response = self._request('POST', endpoint, params={'uploadType': 'media', 'name': record.object_key, 'ifGenerationMatch': '0'}, headers={'Content-Type': 'application/json'}, data=payload)
        if response.status_code != 200:
            raise WitnessError('witness conditional append denied or ambiguous: HTTP ' + str(response.status_code))
        try:
            generation = str(response.json()['generation'])
        except (ValueError, KeyError, TypeError) as exc:
            raise WitnessError('witness missing generation') from exc
        self.verify_exact(record, mac_key, generation)
        return generation

    def verify_exact(self, record: WitnessRecord, mac_key: bytes, generation: str):
        record.verify(mac_key)
        endpoint = 'https://storage.googleapis.com/storage/v1/b/' + quote(self.bucket, safe='') + '/o/' + quote(record.object_key, safe='')
        response = self._request('GET', endpoint, reader=True, params={'alt': 'media', 'generation': generation})
        if response.status_code != 200:
            raise WitnessError('witness readback unavailable: HTTP ' + str(response.status_code))
        if response.content != record.to_bytes():
            raise WitnessError('witness readback mismatch')
        return True
