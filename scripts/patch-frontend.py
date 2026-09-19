#!/usr/bin/env python3
"""Apply Komari frontend reliability fixes to the pinned upstream checkout."""
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if old not in text:
        if new in text:
            return
        raise SystemExit(f"expected frontend source pattern not found: {path}")
    path.write_text(text.replace(old, new, 1))


root = Path(__file__).resolve().parents[1] / "komari-web"
login = root / "src/components/Login.tsx"
replace_once(
    login,
    '''        if (res.status === 200) {\n          refresh();\n          if (typeof onLoginSuccess === "function") {\n            onLoginSuccess();\n            return\n          }\n          window.open("/admin/dashboard", "_self");\n''',
    '''        if (res.status === 200) {\n          // Recreate the document after authentication so stale React/PWA state\n          // cannot reopen an expired route or old lazy-loaded chunk.\n          if (typeof onLoginSuccess === "function") {\n            onLoginSuccess();\n            return;\n          }\n          window.location.replace("/admin/dashboard");\n''',
)
replace_once(
    login,
    '''    const { account, loading, error, refresh } = useAccount();\n''',
    '''    const { account, loading, error } = useAccount();\n''',
)

vite = root / "vite.config.ts"
text = vite.read_text()
old = '''            {\n              urlPattern: /^https:\\/\\/api\\./i,\n              handler: "NetworkFirst",\n              options: {\n                cacheName: "api-cache",\n                expiration: {\n                  maxEntries: 10,\n                  maxAgeSeconds: 60 * 60 * 24 * 365, // <== 365 days\n                },\n                cacheableResponse: {\n                  statuses: [0, 200],\n                },\n              },\n            },'''
new = '''            {\n              // Authentication and monitoring APIs must never be served from\n              // a stale service-worker cache.\n              urlPattern: /^\\/api\\//i,\n              handler: "NetworkOnly",\n            },'''
if new not in text:
    if old not in text:
        raise SystemExit("expected PWA API cache pattern not found")
    vite.write_text(text.replace(old, new, 1))

print("frontend auth/PWA fixes applied")
