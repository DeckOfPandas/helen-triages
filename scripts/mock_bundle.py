"""Bundle a locally built page into one self-contained HTML file for an Artifact.

Restored 2026-09-02 after an agent's tmp/ clean-up removed it. Inlines the
compiled stylesheet (with the woff2 fonts as data URIs), every script the page
loads, and every SVG under assets/img so decorations.js's fetches are answered
from memory instead of the network. Output is body content only (no
<html>/<head>/<body>): the Artifact tool wraps it. Build the site first:
  bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock
"""
import base64, glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(ROOT, "tmp", "site-mock")
BASE = "/helen-triages"


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def font_css(css):
    def rep(m):
        name = m.group(1)
        with open(os.path.join(ROOT, "assets", "fonts", name), "rb") as fh:
            data = base64.b64encode(fh.read()).decode()
        return f'url("data:font/woff2;base64,{data}")'
    return re.sub(r'url\("\.\./fonts/([^"]+)"\)', rep, css)


def svg_map():
    out = {}
    for path in glob.glob(os.path.join(ROOT, "assets", "img", "**", "*.svg"), recursive=True):
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        out[BASE + "/" + rel] = _read(path)
    return out


SHIM = """
(function () {
  var svgs = window.HTF_SVGS || {};
  var orig = window.HTF.fetchSvg;
  window.HTF.fetchSvg = function (url, cb) {
    if (svgs[url]) { cb(svgs[url]); return; }
    orig(url, cb);
  };
})();
"""


def bundle(page, css_file, title, extra_style="", body_transform=None, extra_scripts="", drop_scripts=()):
    html = _read(os.path.join(SITE, page))
    body = re.search(r"<body[^>]*>(.*)</body>", html, re.S).group(1)
    head = re.search(r"<head>(.*)</head>", html, re.S).group(1)
    metas = "\n".join(re.findall(r'<meta name="(?:base-url|site-key)"[^>]*>', head))
    css = font_css(_read(os.path.join(SITE, "assets", "css", css_file)))

    srcs = re.findall(r'<script src="([^"]+)"></script>', html)
    body = re.sub(r'<script src="[^"]+"></script>\s*', "", body)
    body = re.sub(r'href="/helen-triages/[^"]*"', 'href="#" onclick="return false"', body)
    if body_transform:
        body = body_transform(body)

    first, rest = [], []
    for src in srcs:
        rel = src.replace(BASE + "/", "")
        if any(rel.endswith(d) for d in drop_scripts):
            continue
        js = _read(os.path.join(ROOT, rel))
        tag = f"<script>\n{js}\n</script>"
        if rel.endswith("assets/js/assets.js"):
            first.append(tag)
            first.append("<script>window.HTF_SVGS = " + json.dumps(svg_map()) + ";</script>")
            first.append("<script>" + SHIM + "</script>")
        else:
            rest.append(tag)

    # the artifact host lets <main> run full width; pin the site's column
    pin = "\nmain { max-width: 900px !important; margin: 0 auto !important; padding: 2rem 1.5rem !important; }\n"
    return "\n".join([
        f"<title>{title}</title>",
        f"<style>\n{css}\n{pin}{extra_style}\n</style>",
        metas, "\n".join(first), body, "\n".join(rest), extra_scripts,
    ])


def write(out_path, content):
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(out_path, f"{len(content)/1024:.0f} KB")
