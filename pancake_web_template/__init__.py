"""Pancake 模板渲染插件 — Jinja2 模板引擎"""

import logging

from pancake.ovenware import InitAction

logger = logging.getLogger(__name__)


class Main(InitAction):
    """模板渲染插件入口

    init_order=51, 在 web(50) 之后加载。
    通过猴子补丁扩展 web 插件的响应解析，支持模板渲染。
    """

    init_order = 51
    build_order = 0

    def __init__(self):
        from pancake.registry import export

        from pancake_web_template.template import render, template, register_filter
        export(render)
        export(template)
        export(register_filter)

        logger.info("模板渲染插件已加载")

    def build(self):
        """猴子补丁: 扩展 web 插件的 resolve_response"""
        from pancake_web_template.template import _patch_resolve_response
        _patch_resolve_response()
        logger.info("已扩展 web 插件的响应解析（模板渲染支持）")

    def check(self) -> bool:
        """环境检查"""
        try:
            import jinja2
            return True
        except ImportError:
            logger.error("缺少 jinja2 依赖，请执行: pip install jinja2")
            return False
