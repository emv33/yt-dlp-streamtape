import json
import re
import urllib.parse

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError, determine_ext


_BASE_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ),
}

_VIDCONFIG_RE = re.compile(r'var\s+vidconfig\s*=\s*(?P<config>\{.*?\});', re.DOTALL)
_OG_TITLE_RE = re.compile(r'<meta[^>]*\b(?:property|name)=["\']og:title["\'][^>]*>')
_CONTENT_ATTR_RE = re.compile(r'content=["\']([^"\']*)["\']')
_TITLE_TAG_RE = re.compile(r'<title>(.*?)</title>', re.DOTALL)
_TITLE_SUFFIX_RE = re.compile(
    r'\s*(?:[\|\-]\s*Streamtape(?:\.com)?|at\s+Streamtape\.com)\s*$', re.IGNORECASE)
# The page prints the get_video URL inside hidden elements, then rewrites it
# with inline JavaScript substring tricks (the plain HTML value holds a decoy
# token). These regexes replay the string arithmetic to recover the real URL.
_LINK_ASSIGNMENT_RE = re.compile(
    r"""document\.getElementById\(['"](?P<elem>norobotlink|captchalink|ideoooolink)['"]\)
        \.innerHTML\s*=\s*(?P<expr>[^;]+)""", re.VERBOSE)
_LINK_EXPR_RE = re.compile(
    r"""['"](?P<prefix>[^'"]*)['"]\s*\+\s*(?:['"]{2}\s*\+\s*)?\(\s*'
        (?P<body>[^']*)'\s*\)(?P<subs>(?:\.substring\(\d+\))*)""", re.VERBOSE)


def _strip_site_suffix(raw_title):
    return _TITLE_SUFFIX_RE.sub('', raw_title.strip())


def _extract_vidconfig(webpage):
    match = _VIDCONFIG_RE.search(webpage)
    if not match:
        return None
    try:
        return json.loads(match.group('config'))
    except ValueError:
        return None


def _extract_title(webpage, vidconfig, fallback):
    showtitle = (vidconfig or {}).get('showtitle')
    if showtitle:
        return showtitle
    og_tag = _OG_TITLE_RE.search(webpage)
    if og_tag:
        content = _CONTENT_ATTR_RE.search(og_tag.group(0))
        if content:
            return content.group(1)
    title_match = _TITLE_TAG_RE.search(webpage)
    if title_match:
        return _strip_site_suffix(title_match.group(1))
    return fallback


def _deobfuscate_link_expr(expr):
    """
    Evaluate a link-building expression such as
    '//streamtape.com/get_video?id' + ('xcd=...&token=...').substring(1).substring(2)
    """
    match = _LINK_EXPR_RE.search(expr)
    if not match:
        return None
    body = match.group('body')
    for skip in re.findall(r'\.substring\((\d+)\)', match.group('subs')):
        body = body[int(skip):]
    return match.group('prefix') + body


def _build_download_url(webpage, video_id):
    """
    Recover the get_video API URL from the page's anti-bot link script.

    The hidden norobotlink/captchalink elements hold the API URL only after
    the inline JavaScript has run. Replay the .substring() arithmetic and
    verify the resulting URL points at this video.
    """
    candidates = {}
    for match in _LINK_ASSIGNMENT_RE.finditer(webpage):
        candidates.setdefault(match.group('elem'), match.group('expr'))
    for element in ('norobotlink', 'captchalink', 'ideoooolink'):
        expr = candidates.get(element)
        if not expr:
            continue
        link = _deobfuscate_link_expr(expr)
        if not link:
            continue
        if link.startswith('//'):
            link = 'https:' + link
        elif link.startswith('/'):
            # The page's player concatenates 'https:/' with these.
            link = 'https:/' + link
        parsed = urllib.parse.urlparse(link)
        if urllib.parse.parse_qs(parsed.query).get('id') == [video_id]:
            return link
    return None


class StreamtapeIE(InfoExtractor):
    IE_NAME = 'streamtape'
    IE_DESC = 'streamtape.* video/file'
    # An optional trailing /<file-name> (e.g. /VishnuPriya.mp4) is ignored.
    _VALID_URL = r'https?://(?:www\.)?streamtape\.\w+/(?:v|e)/(?P<id>[\w-]+)(?:/[^/?#]*)?'

    # TODO: add a full live test (with info_dict) — Streamtape content is
    # frequently taken down, so keep these URLs up to date.
    _TESTS = [
        {
            'url': 'https://streamtape.com/v/vLM7MDqR9rS4RXv',
            'only_matching': True,
        },
        {
            'url': 'https://streamtape.com/v/vLM7MDqR9rS4RXv/VishnuPriya.mp4',
            'only_matching': True,
        },
        {
            'url': 'https://streamtape.com/e/vLM7MDqR9rS4RXv',
            'only_matching': True,
        },
        {
            'url': 'https://streamtape.com/e/vLM7MDqR9rS4RXv/VishnuPriya.mp4',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # Normalise embed (/e/) links to the canonical /v/ page,
        # dropping any trailing file name.
        url = f'https://streamtape.com/v/{video_id}'

        webpage = self._download_webpage(
            url, video_id, headers={**_BASE_HEADERS, 'Referer': 'https://streamtape.com/'},
        )

        vidconfig = _extract_vidconfig(webpage)
        media_url = _build_download_url(webpage, video_id)
        if not media_url:
            raise ExtractorError(
                f'Could not find the download URL on Streamtape page {video_id!r} '
                '(the page structure changed)',
                expected=True,
            )

        title = _extract_title(webpage, vidconfig, fallback=video_id)
        ext = determine_ext(urllib.parse.urlparse(media_url).path, default_ext='mp4')

        return {
            'id': video_id,
            'title': title,
            'url': media_url,
            'ext': ext,
            # The page actually downloaded is the canonical /v/ URL; yt-dlp
            # derives webpage_url_basename/webpage_url_domain from this.
            'webpage_url': url,
            'http_headers': {**_BASE_HEADERS, 'Referer': url},
        }
