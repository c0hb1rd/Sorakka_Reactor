class SorakaRoutine:
    def process(self, header, params, socket):
        raise NotImplementedError

    @classmethod
    def get_func(cls, name):
        def func(*args, **kwargs):
            obj = func.view_class()

            return obj.process(*args, **kwargs)

        func.view_class = cls
        func.__doc__ = cls.__doc__
        func.__module__ = cls.__module__
        func.__name__ = name

        return func

