import hmac
import ipaddress
import re

import requests
from CloudFlare import CloudFlare
from CloudFlare.exceptions import CloudFlareAPIError
from flask import Flask, request, abort, Response
from requests import ReadTimeout

from src.logger import init_logger
from src.config import config_instance
from src.config import is_development


DEFAULT_IPV4 = ['173.245.48.0/20', '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22',
                '141.101.64.0/18', '108.162.192.0/18', '190.93.240.0/20', '188.114.96.0/20',
                '197.234.240.0/22', '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13',
                '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22']

# Define dictionary of malicious patterns
malicious_patterns = {
    "buffer_overflow": "^\?unix:A{1000,}",  # pattern for buffer overflow attack
    "SQL_injection": "'?([\w\s]+)'?\s*OR\s*'?([\w\s]+)'?\s*=\s*'?([\w\s]+)'?",  # pattern for SQL injection attack
    "SQL_injection_Commands": "\b(ALTER|CREATE|DELETE|DROP|EXEC(UTE){0,1}|INSERT( +INTO){0,1}|MERGE|REPLACE|SELECT|UPDATE)\b",
    # Match SQL Commands
    "SQL_injection_Comments": "(--|#|\/\*)[\w\d\s]*",  # Match SQL Comments
    "SQL_Injection_syntax": "\b(AND|OR)[\s]*[^\s]*=[^\s]*",  # Match SQL Injection Syntax
    "SQL_Union_select_attack": "(?i)\bselect\b.*\bfrom\b.*\bunion\b.*\bselect\b",  # UNION Select Attack
    "SQL_BLIND_SQL_Injection": "(?i)\b(if|case).*\blike\b.*\bthen\b",  # blind SQL Injection attack
    "SQL_TIMEBASED_Injection": "(?i)\b(select|and)\b.*\bsleep\(\d+\)\b",  # Time based injection attacks
    "XSS": "<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",  # pattern for cross-site scripting (XSS) attack
    "path_traversal": "\.\.[\\\/]?|\.[\\\/]{2,}",  # pattern for path traversal attack
    # "LDAP_injection": "[()\\\/*\x00-\x1f\x80-\xff]",  # pattern for LDAP injection attack
    "command_injection": ";\s*(?:sh|bash|cmd|powershell)\b",  # pattern for command injection attack
    "file_inclusion": "(?:file|php|zip|glob|data)\s*:",  # pattern for file inclusion attack
    "RCE_attack": "^.*\b(?:eval|assert|exec|system|passthru|popen|proc_open)\b.*$",
    # pattern for remote code execution attack
    "CSRF_attack": "^.*(GET|POST)\s+.*\b(?:referer|origin)\b\s*:\s*(?!https?://(?:localhost|127\.0\.0\.1)).*$",
    # # pattern for cross-site request forgery attack
    "SSRF_attack": "^.*\b(?:curl|wget|file_get_contents|fsockopen|stream_socket_client|socket_create)\b.*$",
    # pattern for server-side request forgery attack
    "CSWSH_attack": "^.*\b(?:Sec-WebSocket-Key|Sec-WebSocket-Accept)\b.*$",
    "BRUTEFORCE_attack": "^.*\b(?:admin|root|test|user|guest)\b.*$",
    "Credential_Stuffing": "(?:\badmin\b|\broot\b|\bpassword\b|\b123456\b|\bqwerty\b|\b123456789\b|\b12345678\b|\b1234567890\b|\b12345\b|\b1234567\b|\b12345678910\b|\b123123\b|\b1234\b|\b111111\b|\babc123\b|\bmonkey\b|\bdragon\b|\bletmein\b|\bsunshine\b|\bprincess\b|\b123456789\b|\bfootball\b|\bcharlie\b|\bshadow\b|\bmichael\b|\bjennifer\b|\bcomputer\b|\bsecurity\b|\btrustno1\b)",
    # "Remote_File_Inclusion": "^.*(include|require)(_once)?\s*\(?\s*[\]\s*(https?:)?//",
    "Clickjacking": '<iframe\s*src="[^"]+"|<iframe\s*src=\'[^\']+\'|\bX-Frame-Options\b\s*:\s*\b(DENY|SAMEORIGIN)\b',
    "XML_External_Entity_Injection": "<!ENTITY[^>]*>",
    "Server_Side_Template_Injection": "\{\{\s*(?:config|app|request|session|env|get|post|server|cookie|_|\|\|)\..+?\}\}",
    "Business_Logic_Attacks": "^\b(?:price|discount|quantity|shipping|coupon|tax|refund|voucher|payment)\b",
    "Javascript_injection": "(?:<\sscript\s>\s*|\blocation\b\s*=|\bwindow\b\s*.\slocation\s=|\bdocument\b\s*.\slocation\s=)",
    "HTML_injection": "<\siframe\s|<\simg\s|<\sobject\s|<\sembed\s",
    # "HTTP_PARAMETER_POLLUTION":  '(?<=^|&)[\w-]+=[^&]*&[\w-]+=',
    "DOM_BASED_XSS": "(?:\blocation\b\s*.\s*(?:hash|search|pathname)|document\s*.\s*(?:location|referrer).hash)"
}


def contains_malicious_patterns(_input: str) -> bool:
    """
    **contains_malicious_patterns**
        will return true if the string matches any of the attack patterns
    :param _input:
    :return:
    """
    attack_pattern = r"\b(select|update|delete|drop|create|alter|insert|into|from|where|union|having|or|and|exec|script|javascript|xss|sql|cmd|buffer|format|include|shell|rfi|lfi|phish)\b"
    return re.search(attack_pattern, _input, re.IGNORECASE) is not None


EMAIL: str = config_instance().CLOUDFLARE_SETTINGS.EMAIL
TOKEN: str = config_instance().CLOUDFLARE_SETTINGS.TOKEN


class Firewall:
    """
        used in conjunction with cloudflare to secure requests to this web application
        by using several methods including IP White listing

    """

    def __init__(self):
        self.allowed_hosts = config_instance().HOST_ADDRESSES.split(",")
        self._max_payload_size: int = 8 * 64
        try:
            self.cloud_flare = CloudFlare(email=EMAIL, token=TOKEN)
        except CloudFlareAPIError:
            pass
        self.ip_ranges = []
        self.bad_addresses = set()
        self.compiled_bad_patterns = [re.compile(pattern) for pattern in malicious_patterns.values()]
        self._logger = init_logger(self.__class__.__name__)

    def init_app(self, app: Flask):
        # Setting Up Incoming Request Security Checks
        if not is_development():
            # if this is not a development server secure the server with our firewall
            app.before_request(self.is_host_valid)
            app.before_request(self.is_edge_ip_allowed)
            app.before_request(self.check_if_request_malicious)
            app.before_request(self.verify_client_secret_token)

            # Setting up Security headers for outgoing requests
            app.after_request(self.add_security_headers)
            #
        # obtain the latest cloudflare edge servers
        ipv4, ipv6 = self.get_ip_ranges()
        # updating the ip ranges
        self.ip_ranges.extend(ipv4)
        self.ip_ranges.extend(ipv6)

    def is_host_valid(self):
        """
        **is_host_valid**
            will return true if host is one of the allowed hosts addresses
            and both request host and header matches
        """
        header_host = request.headers.get('Host')
        self._logger.info(f'Host is : {header_host}')
        self._logger.info(f'allowed hosts : {self.allowed_hosts}')

        if header_host.casefold() != request.host.casefold():
            abort(401, 'Bad Host Header')
        if request.host not in self.allowed_hosts:
            abort(401, 'Host not allowed')

    def is_edge_ip_allowed(self):
        """
        **is_edge_ip_allowed**
            checks if edge ip falls within known cloudflare ip ranges
        """
        edge_ip = self.get_edge_server_ip(headers=request.headers)
        if not any(ipaddress.ip_address(edge_ip) in ipaddress.ip_network(ip_range) for ip_range in self.ip_ranges):
            abort(401, 'IP Address not allowed')

    def check_if_request_malicious(self):
        """
        **check_if_request_malicious**
            Analyses request headers , body and path if there
            are any malicious patterns an error will be thrown
        """
        # Check request for malicious patterns
        headers: dict[str, str] = request.headers
        body = request.data

        if 'Content-Length' in headers and int(headers['Content-Length']) > self._max_payload_size:
            # Request payload is too large,
            self._logger.info("Payload too long")
            abort(401, 'Payload is suspicious')

        if body:
            _body = body.decode('utf-8')
            if contains_malicious_patterns(_input=_body):
                self._logger.info("Payload regex failure")
                abort(401, 'Payload is suspicious')

        path = str(request.path)
        if any((pattern.match(path) for pattern in self.compiled_bad_patterns)):
            self._logger.info("Attack patterns regex failure on path")
            abort(401, 'Request path is malformed')

    @staticmethod
    def verify_client_secret_token():
        """
        **verify_client_secret_token**
            check if cloud_flare signed the request with a secret token
        :return:
        """
        client_secret_token = request.headers.get('X-CLIENT-SECRET-TOKEN')
        if not client_secret_token:
            abort(401, 'Request not Authenticated - token missing')

        expected_secret_token = config_instance().CLOUDFLARE_SETTINGS.X_CLIENT_SECRET_TOKEN
        if not expected_secret_token:
            abort(401, 'Request not Authenticated')

        if not hmac.compare_digest(client_secret_token, expected_secret_token):
            abort(401, 'Request Origin not Trusted - token mismatch')

    @staticmethod
    def get_client_ip() -> str:
        """
        **get_client_ip**
            will return the actual client ip address of the client making the request
        """
        ip = request.headers.get('cf-connecting-ip')
        return ip.split(',')[0]

    @staticmethod
    def get_edge_server_ip(headers) -> str:
        """
        **get_edge_server_ip**
            obtains cloudflare edge server the request is being routed through
        """
        return headers.get("x-real-ip")

    @staticmethod
    def get_ip_ranges() -> tuple[list[str], list[str]]:
        """
        **get_ip_ranges**
            obtains a list of ip addresses from cloudflare edge servers
        :return:
        """
        _uri = 'https://api.cloudflare.com/client/v4/ips'
        _headers = {'Accept': 'application/json', 'X-Auth-Email': EMAIL}
        try:
            with requests.Session() as send_request:
                try:
                    response = send_request.get(url=_uri, headers=_headers)
                    response_data: dict[str, dict[str, str] | list[str]] = response.json()
                    ipv4_cidrs = response_data.get('result', {}).get('ipv4_cidrs', DEFAULT_IPV4)
                    ipv6_cidrs = response_data.get('result', {}).get('ipv6_cidrs', [])
                    return ipv4_cidrs, ipv6_cidrs
                except (ConnectionError, ReadTimeout):
                    return [], []

        except CloudFlareAPIError:
            return [], []

    @staticmethod
    def add_security_headers(response: Response) -> Response:
        """
            **add_security_headers**
                the headers below are meant to secure the website from malicious attacks
        :param response:
        :return:
        """

        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        session_cookies = [request.cookies.get('auth')]
        session_cookies = [cookie for cookie in session_cookies if cookie is not None]
        if session_cookies:
            response.headers['Session-Vary'] = 'auth'

        # exempting redoc & blog from content security policies except frame and XSS
        if bypass_content_security_policy():
            return response

        response.headers['Content-Security-Policy'] = "default-src 'self' https://static.cloudflareinsights.com https://fonts.googleapis.com https://www.googletagmanager.com https://netdna.bootstrapcdn.com https://t.paypal.com https://www.paypal.com https://www.cloudflare.com https://www.google-analytics.com https://fonts.gstatic.com; img-src 'self' https://www.paypalobjects.com;"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response


def bypass_content_security_policy() -> bool:
    # if request.url.casefold() == 'https://eod-stock-api.site/redoc':
    #     return True
    # if request.url.casefold().startswith('https://eod-stock-api.site/blog'):
    #     return True
    return False
