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

_OG_TITLE_RE = re.compile(r'<meta\s+property="og:title"\s+content="([^"]*)"')
_TITLE_TAG_RE = re.compile(r'<title>(.*?)</title>', re.DOTALL)
_TITLE_SUFFIX_RE = re.compile(r'\s*[\|\-]\s*Streamtape(?:\.com)?\s*$', re.IGNORECASE)


def _strip_site_suffix(raw_title):
    return _TITLE_SUFFIX_RE.sub('', raw_title.strip())


def _extract_title(webpage, fallback):
    og_match = _OG_TITLE_RE.search(webpage)
    if og_match:
        return og_match.group(1)
    title_match = _TITLE_TAG_RE.search(webpage)
    if title_match:
        return _strip_site_suffix(title_match.group(1))
    return fallback


def _extract_download_url(webpage):
    """
    TODO: Parse the direct media URL out of the file page.

    Streamtape builds the download link with inline JavaScript on the page
    (the element is usually targeted by an id such as `robotlink`). Inspect a
    live page with `--verbose` or curl and implement the parsing here.
    Return the absolute URL, or None if it cannot be found.
    """
    return None


class StreamtapeIE(InfoExtractor):
    IE_NAME = 'streamtape'
    IE_DESC = 'streamtape.* video/file'
    # An optional trailing /<file-name> (e.g. /VishnuPriya.mp4) is ignored.
    _VALID_URL = r'https?://(?:www\.)?streamtape\.\w+/(?:v|e)/(?P<id>[\w-]+)(?:/[^/?#]*)?'

    # TODO: add real, live URLs once extraction works. Streamtape content is
    # frequently taken down, so keep these up to date.
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

        media_url = _extract_download_url(webpage)
        if not media_url:
            raise ExtractorError(
                f'Could not find the download URL on Streamtape page {video_id!r} '
                '(extractor not implemented yet, or the page structure changed)',
                expected=True,
            )

        title = _extract_title(webpage, fallback=video_id)
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
