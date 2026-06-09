"""Jinja2 模板引擎封装"""

import logging
import os

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

_env: Environment = None


def _get_env() -> Environment:
    """获取或创建 Jinja2 Environment（单例）"""
    global _env
    if _env is None:
        from pancake import settings

        template_dir = settings.get("pancake.web.templates") or os.path.join("src", "templates")
        debug = settings.get("pancake.web.debug") or False

        if not os.path.isdir(template_dir):
            os.makedirs(template_dir, exist_ok=True)
            logger.info(f"模板目录已创建: {template_dir}")

        loader = FileSystemLoader(template_dir)
        _env = Environment(loader=loader, auto_reload=debug)
        logger.info(f"Jinja2 引擎已初始化: {template_dir}")
    return _env


def render(template_name: str, **context):
    """渲染模板，返回 HtmlResponse

    Usage:
        return render("home.html", title="首页", items=[1, 2, 3])
    """
    from pancake_web.response import HtmlResponse

    env = _get_env()
    tmpl = env.get_template(template_name)
    html = tmpl.render(**context)
    return HtmlResponse(html)


def template(template_name: str):
    """@template — 标记 handler 使用的模板名

    handler 返回 dict 时自动渲染为 HTML 页面。

    Usage:
        @get("/home")
        @template("home.html")
        async def home(self, request):
            return {"title": "首页", "items": [1, 2, 3]}
    """
    def decorator(func):
        func._template_name = template_name
        return func
    return decorator


def register_filter(name: str, func):
    """注册 Jinja2 自定义过滤器

    Usage:
        register_filter("reverse", lambda s: s[::-1])
    """
    env = _get_env()
    env.filters[name] = func
    logger.debug(f"注册模板过滤器: {name}")


def _patch_resolve_response():
    """猴子补丁: 扩展 web 插件的 resolve_response，支持 @template 自动渲染"""
    import pancake_web.decorators as web_decorators

    _original_resolve = web_decorators.resolve_response

    async def _patched_resolve(result, _handler=None):
        # 如果 handler 有 @template 标记且返回 dict，渲染模板
        if _handler and isinstance(result, dict) and hasattr(_handler, "_template_name"):
            logger.info(f"渲染模板: {_handler._template_name}")
            return render(_handler._template_name, **result)
        return await _original_resolve(result)

    web_decorators.resolve_response = _patched_resolve
    logger.debug("resolve_response 已补丁")


def reset_env():
    """重置 Jinja2 环境（用于测试）"""
    global _env
    _env = None
