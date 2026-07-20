def info(self, event: str, *args, **kw):
        """INFO 级别（常规信息）。
        兼容两种写法：① logger.info("事件", key=value)；② logger.info("模板 %s", 值)。
        （*args 接收任意多个「位置参数」，用于支持第二种老写法）"""
        if args:                               # 如果传了位置参数，说明是「模板 + 值」的老写法
            self._log.info(event, *args)       # 直接交给标准库做 % 占位符格式化
        else:                                  # 否则按结构化写法处理
            self._log.info(self._fmt(event, **kw))

def warning(self, event: str, *args, **kw):
    """WARNING 级别（警告：不影响运行但需注意）"""
    if args:
        self._log.warning(event, *args)
    else:
        self._log.warning(self._fmt(event, **kw))