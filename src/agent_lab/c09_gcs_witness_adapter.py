"""Bounded GCS witness adapter. Not wired into protected Kernel operations.

Caller supplies independent credentials and MAC key; never logs them.
"""
from __future__ import annotations

from urllib.parse import quote
import re

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

    def append_authenticated(self,record_bytes: bytes):
        """Transport exact Custodian output; public parsing confers no authenticity."""
        record=WitnessRecord.from_public_bytes(record_bytes)
        endpoint='https://storage.googleapis.com/upload/storage/v1/b/'+quote(self.bucket,safe='')+'/o'
        response=self._request('POST',endpoint,params={'uploadType':'media','name':record.object_key,'ifGenerationMatch':'0'},headers={'Content-Type':'application/json'},data=record_bytes)
        if response.status_code!=200:raise WitnessError('conditional append denied or ambiguous: HTTP '+str(response.status_code))
        try:generation=str(response.json()['generation'])
        except (ValueError,KeyError,TypeError) as exc:raise WitnessError('generation unavailable') from exc
        if not re.fullmatch(r'[1-9][0-9]{0,29}',generation):raise WitnessError('invalid generation')
        self.readback_authenticated(record_bytes,generation)
        return generation

    def readback_authenticated(self,record_bytes: bytes,generation: str):
        record=WitnessRecord.from_public_bytes(record_bytes)
        if not isinstance(generation,str) or not re.fullmatch(r'[1-9][0-9]{0,29}',generation):raise WitnessError('invalid exact generation')
        endpoint='https://storage.googleapis.com/storage/v1/b/'+quote(self.bucket,safe='')+'/o/'+quote(record.object_key,safe='')
        response=self._request('GET',endpoint,reader=True,params={'alt':'media','generation':generation})
        if response.status_code!=200 or response.content!=record_bytes:raise WitnessError('exact authenticated bytes readback mismatch')
        return response.content

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
        raw = self._read_complete_chain_objects(deployment_id)
        records: list[WitnessRecord] = []
        for name, generation, payload in raw:
            record = WitnessRecord.from_bytes(payload, mac_key)
            if record.object_key != name:
                raise WitnessError('witness object key mismatch')
            records.append(record)
        return verify_chain(records, mac_key, deployment_id=deployment_id)

    def read_complete_chain(self, deployment_id: str) -> tuple[tuple[str, bytes], ...]:
        """WitnessClient-compatible generation/bytes view of the complete chain."""
        output=[]
        for name,generation,payload in self._read_complete_chain_objects(deployment_id):
            if WitnessRecord.from_public_bytes(payload).object_key!=name:raise WitnessError('Witness content/object-key substitution')
            output.append((generation,payload))
        return tuple(output)

    def _read_complete_chain_objects(self, deployment_id: str) -> tuple[tuple[str, str, bytes], ...]:
        """Read every strongly-listed generation; any pagination ambiguity denies."""
        if not deployment_id:
            raise WitnessError('deployment identity unavailable')
        endpoint = 'https://storage.googleapis.com/storage/v1/b/' + quote(self.bucket, safe='') + '/o'
        observed: dict[str, str] = {}
        prefix = f'witness/v1/{deployment_id}/'
        page_token: str | None = None
        seen_tokens: set[str] = set()
        while True:
            params = {'prefix': prefix, 'versions': 'true'}
            if page_token is not None:
                params['pageToken'] = page_token
            response = self._request('GET', endpoint, reader=True, params=params)
            if response.status_code != 200:
                raise WitnessError('witness listing unavailable: HTTP ' + str(response.status_code))
            try:
                listing = response.json()
            except ValueError as exc:
                raise WitnessError('invalid witness listing') from exc
            if not isinstance(listing, dict) or set(listing) - {'items', 'nextPageToken'}:
                raise WitnessError('invalid witness listing')
            items = listing.get('items', [])
            if not isinstance(items, list):
                raise WitnessError('invalid witness listing')
            for item in items:
                if not isinstance(item, dict) or set(item) - {'name', 'generation', 'size', 'timeDeleted'}:
                    raise WitnessError('ambiguous witness metadata')
                name = item.get('name')
                generation = item.get('generation')
                if (
                    not isinstance(name, str) or not name.startswith(prefix)
                    or not isinstance(generation, str) or not re.fullmatch(r'[1-9][0-9]{0,29}',generation)
                    or item.get('timeDeleted') is not None
                    or name in observed
                ):
                    raise WitnessError('multiple versions, deletion, or invalid witness metadata')
                observed[name] = generation
            next_token = listing.get('nextPageToken')
            if next_token is None:
                break
            if not isinstance(next_token, str) or not next_token or len(next_token) > 1024 or next_token in seen_tokens:
                raise WitnessError('invalid or repeated witness page token')
            seen_tokens.add(next_token)
            page_token = next_token
        records: list[tuple[str, str, bytes]] = []
        for name in sorted(observed):
            object_endpoint = endpoint + '/' + quote(name, safe='')
            download = self._request(
                'GET', object_endpoint, reader=True,
                params={'alt': 'media', 'generation': observed[name]},
            )
            if download.status_code != 200:
                raise WitnessError('witness generation readback unavailable: HTTP ' + str(download.status_code))
            records.append((name, observed[name], download.content))
        return tuple(records)
