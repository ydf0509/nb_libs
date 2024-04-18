

from decorator_libs import cached_method_result,SingletonBaseNew

class LazyImpoter(SingletonBaseNew):
    """
    延迟导入,避免需要互相导入.
    """

    @property
    @cached_method_result
    def gvent_patch_all(self):
        from gevent import monkey
        return monkey.patch_all



lazy_impoter = LazyImpoter()

if __name__ == '__main__':
    pass
    # lazy_impoter.gvent_patch_all()
    from gevent import monkey
    monkey.patch_all()

