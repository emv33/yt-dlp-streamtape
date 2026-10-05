# yt-dlp-streamtape

A yt-dlp plugin adding native support for streamtape.* video pages (`/v/`, `/e/`).

> Deobfuscates the `get_video` API URL from the page's anti-bot link script and reads the title from `vidconfig`.

## Installing

Install from a local checkout (the plugin is not published to PyPI):

```bash
pip install /path/to/yt-dlp-streamtape
# or, for development:
pip install -e /path/to/yt-dlp-streamtape
```

Alternatively, copy the `yt_dlp_plugins/` folder into one of yt-dlp's plugin
directories, e.g. `${XDG_CONFIG_HOME}/yt-dlp/plugins/yt-dlp-streamtape/`.

Verify it loaded:

```bash
yt-dlp --verbose 2>&1 | grep -i plugin
```

The output should include `StreamtapeIE`.

## Usage

Once implemented, use it like any other yt-dlp site:

```bash
yt-dlp https://streamtape.com/v/<id>/<name>
```

Run with `--verbose` and check that the log shows `[streamtape]` rather than `[generic]`.

## Status

- [x] Plugin package layout and `pyproject.toml`
- [x] `StreamtapeIE` registered for `streamtape.*` `/v/`, `/e/` URLs
- [x] Deobfuscate the `get_video` URL from the page's anti-bot link script
- [ ] Add `_TESTS` with live URLs
- [ ] Decide whether a playlist/account extractor is needed

## Legal Notice

**yt-dlp-streamtape** is an independent project and is not affiliated with, authorized,
maintained, or endorsed by yt-dlp or Streamtape. It is provided for educational and
personal archival purposes only. Users are responsible for complying with the Terms of
Service of the platforms they use and the copyrights of the content creators.
