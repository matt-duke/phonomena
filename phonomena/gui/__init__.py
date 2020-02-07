"""import os
__all__ = []
print(__file__)
for f in os.listdir(os.path.dirname(os.path.realpath(__file__))):
    if f.endswith('.py') and f != '__init__':
        __all__.append(f[:-3])
del f, os"""
