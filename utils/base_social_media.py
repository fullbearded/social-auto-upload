from pathlib import Path
from typing import List

from conf import BASE_DIR, LOCAL_CHROME_PATH

SOCIAL_MEDIA_DOUYIN = "douyin"
SOCIAL_MEDIA_TENCENT = "tencent"
SOCIAL_MEDIA_TIKTOK = "tiktok"
SOCIAL_MEDIA_BILIBILI = "bilibili"
SOCIAL_MEDIA_KUAISHOU = "kuaishou"


def get_supported_social_media() -> List[str]:
    return [SOCIAL_MEDIA_DOUYIN, SOCIAL_MEDIA_TENCENT, SOCIAL_MEDIA_TIKTOK, SOCIAL_MEDIA_KUAISHOU]


def get_cli_action() -> List[str]:
    return ["upload", "login", "watch"]


# Chrome args: 减少 Chrome 自身开销（更新检查、同步、扩展等），不影响 patchright 反检测
_CHROME_PERF_ARGS = [
    "--disable-extensions",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-background-networking",
    "--disable-sync",
    "--no-first-run",
    "--disable-features=TranslateUI",
    "--disable-ipc-flooding-protection",
]

_BROWSER_DATA_DIR = Path(BASE_DIR) / "browser_data"


def get_user_data_dir(platform: str, account: str) -> Path:
    dir_path = _BROWSER_DATA_DIR / platform / account
    dir_path.mkdir(parents=True, exist_ok=True)
    singleton_lock = dir_path / "SingletonLock"
    if singleton_lock.exists():
        singleton_lock.unlink(missing_ok=True)
    return dir_path


def _parse_platform_account_from_cookie_file(account_file: str | Path) -> tuple[str, str]:
    stem = Path(account_file).stem
    if "_" in stem:
        platform, account = stem.split("_", 1)
    else:
        platform, account = stem, stem
    return platform, account


def get_user_data_dir_from_cookie_file(account_file: str | Path) -> Path:
    platform, account = _parse_platform_account_from_cookie_file(account_file)
    return get_user_data_dir(platform, account)


def has_user_data_dir(account_file: str | Path) -> bool:
    user_data_dir = get_user_data_dir_from_cookie_file(account_file)
    return user_data_dir.exists() and any(user_data_dir.iterdir())


def build_stealth_launch_kwargs(headless: bool = True) -> dict:
    kwargs: dict = {
        "headless": headless,
        "args": _CHROME_PERF_ARGS,
    }
    if LOCAL_CHROME_PATH:
        kwargs["executable_path"] = LOCAL_CHROME_PATH
    else:
        kwargs["channel"] = "chrome"
    return kwargs


def build_persistent_context_kwargs(headless: bool = True) -> dict:
    """launch_persistent_context 的参数：含 Chrome 性能优化 args + no_viewport。"""
    kwargs: dict = {
        "headless": headless,
        "args": _CHROME_PERF_ARGS,
        "no_viewport": True,
    }
    if LOCAL_CHROME_PATH:
        kwargs["executable_path"] = LOCAL_CHROME_PATH
    else:
        kwargs["channel"] = "chrome"
    return kwargs


async def set_init_script(context):
    return context
