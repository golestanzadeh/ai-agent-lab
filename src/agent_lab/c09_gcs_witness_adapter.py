"""Bounded GCS witness adapter. Not wired into protected Kernel operations.

Caller supplies independent credentials and MAC key; never logs them.
"""
from __future__ import annotations

from urllib.parse import quote

import requests
from .c09_witness_protocol import WitnessError, WitnessRecord, verify_chain


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

    def read_chain(self, deployment_id: str, mac_key: bytes) -> tuple[WitnessRecord, ...]:
        if not deployment_id:
            raise WitnessError('deployment identity unavailable')
        endpoint = 'https://storage.googleapis.com/storage/v1/b/' + quote(self.bucket, safe='') + '/o'
        response = self._request(
            'GET', endpoint, reader=True,
            params={'prefix': f'witness/v1/{deployment_id}/', 'versions': 'true'},
        )
        if response.status_code != 200:
            raise WitnessError('witness listing unavailable: HTTP ' + str(response.status_code))
        try:
            listing = response.json()
            items = listing.get('items', [])
        except (ValueError, AttributeError) as exc:
            raise WitnessError('invalid witness listing') from exc
        if not isinstance(items, list):
            raise WitnessError('invalid witness listing')
        observed: dict[str, str] = {}
        prefix = f'witness/v1/{deployment_id}/'
        for item in items:
            if not isinstance(item, dict) or set(item) - {'name', 'generation', 'size', 'timeDeleted'}:
                raise WitnessError('ambiguous witness metadata')
            name = item.get('name')
            generation = item.get('generation')
            if (
                not isinstance(name, str) or not name.startswith(prefix)
                or not isinstance(generation, str) or not generation.isdigit()
                or item.get('timeDeleted') is not None
                or name in observed
            ):
                raise WitnessError('multiple versions, deletion, or invalid witness metadata')
            observed[name] = generation
        records: list[WitnessRecord] = []
        for name in sorted(observed):
            object_endpoint = endpoint + '/' + quote(name, safe='')
            download = self._request(
                'GET', object_endpoint, reader=True,
                params={'alt': 'media', 'generation': observed[name]},
            )
            if download.status_code != 200:
                raise WitnessError('witness generation readback unavailable: HTTP ' + str(download.status_code))
            record = WitnessRecord.from_bytes(download.content, mac_key)
            if record.object_key != name:
                raise WitnessError('witness object key mismatch')
            records.append(record)
        return verify_chain(records, mac_key, deployment_id=deployment_id)
