
import json
import logging
import datetime

from signing import RequestSigner

import requests

class APIError(Exception):
    pass

logger = logging.getLogger('blocked.api')


class BaseApiClient(object):
    API = 'https://api.blocked.org.uk/1.2/'
    def __init__(self, username, secret):
        self.username = username
        self.secret = secret
        self.signer = RequestSigner(self.secret)
        self.sign = self.signer.get_signature

    def timestamp(self):
        return datetime.datetime.utcnow().strftime(
            '%Y%m%d-%H:%M:%S'
            )

    def GET(self, url, data,decode=True, _stream=False):
        data['email'] = self.username
        try:
            req = requests.get(self.API + url, params=data, stream=_stream)
            logger.info("Status: %s", req.status_code)
            if _stream:
                return req.iter_lines()
            elif decode:
                logger.debug("Return: %s", req.content)
                json = req.json()
                if 'success' in json and json['success'] != True:
                    raise APIError(json['error'])
                return json
            else:
                return req.content
        except Exception as exc:
            raise
            raise APIError(*exc.args)

    def POST(self, url, data):
        data['email'] = self.username
        try:
            req = requests.post(self.API + url, data=data)
            logger.info("Status: %s", req.status_code)
            return req.json()
        except Exception as exc:
            raise APIError(*exc.args)

    def DELETE(self, url, data):
        data['email'] = self.username
        try:
            req = requests.delete(self.API + url, params=data)
            logger.info("Status: %s", req.status_code)
            return req.json()
        except Exception as exc:
            raise APIError(*exc.args)
    
    def POST_JSON(self, url, data):
        req = requests.post(self.API + url, data=json.dumps(data),
            headers={'Content-type': 'application/javascript'})
        return req.json()

class ApiClient(BaseApiClient):
    SIGNATURES = {
        'search/url': ['q'],
        'status/probes': ['date'],
        'status/url': ['url'],
        'status/blocks': ['date'],
        'status/ispreports': ['date'],
        'status/stats': ['date'],
        'status/isp-stats': ['date'],
        'status/category-stats': ['date'],
        'status/domain-isp-stats': ['date'],
        'status/domain-stats': ['date'],
        'ispreport/blacklist': ['date'],
        }

    def _request(self, endpoint, req):
        try:
            req['signature'] = self.sign(req, self.SIGNATURES[endpoint])
        except KeyError:
            for k,v in self.SIGNATURES.iteritems():
                if endpoint.startswith(k):
                    req['signature'] = self.sign(req, v)
                    break
        data = self.GET(endpoint, req)
        return data

    def search_url(self, search, page=0, exclude_adult=0):
        """Search sites by keyword"""

        req = {'q': search, 'page': page, 'exclude_adult': exclude_adult}
        return self._request('search/url', req)

    def recent_blocks(self, page, region, format='networkrow', sort='url'):
        req = {'date': self.timestamp(), 'page': str(page), 'format': format, 'sort': sort}
        return self._request('status/blocks/'+region, req)

    def stats(self):
        req = {'date': self.timestamp()}
        return self._request('status/stats', req)

    def reports(self, page, isp=None):
        req = {'date': self.timestamp(), 'page': str(page)}
        if isp:
            req['isp'] = isp
        return self._request('status/ispreports', req)

    def isp_stats(self):
        req = {'date': self.timestamp()}
        return self._request('status/isp-stats', req)

    def category_stats(self):
        req = {'date': self.timestamp()}
        return self._request('status/category-stats', req)

    def domain_stats(self):
        req = {'date': self.timestamp()}
        return self._request('status/domain-stats', req)

    def domain_isp_stats(self):
        req = {'date': self.timestamp()}
        return self._request('status/domain-isp-stats', req)

    def status_url(self, url):
        req = {'url': url}
        return self._request('status/url', req)

    def status_probes(self):
        req = {'date':self.timestamp()}
        return self._request('status/probes', req)


    def blacklist_insert(self, domain):
        req = {'date': self.timestamp(), 'domain': domain}
        req['signature'] = self.sign(req, ['date','domain'])
        return self.POST('ispreport/blacklist', req)

    def blacklist_select(self):
        req = {'date': self.timestamp()}
        return self._request('ispreport/blacklist', req)


    def blacklist_delete(self, domain):
        req = {'date': self.timestamp(), 'domain': domain}
        req['signature'] = self.sign(req, ['date','domain'])
        return self.DELETE('ispreport/blacklist', req)


