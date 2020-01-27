try:
    import ConfigParser as configparser
except ModuleNotFoundError:
    import configparser


class CfgReader(object):
    """
    A simple utility class that encapsulates read-only access
    to parameters stored in a ConfigParser style config file.

    For example, if the .cfg file has the following:

        [section]
        foo = bar

    Then this object will have a member, section.foo,
    with the value, "bar".
    """

    class Section(object):
        def __setattr__(self, name, value):
            raise Exception("This object is read only")

    def __init__(self, cfg_filename):
        config = configparser.SafeConfigParser()
        with open(cfg_filename, "r") as f:
            config.readfp(f)

        for section in config.sections():
            s = CfgReader.Section()
            for option in config.options(section):
                s.__dict__[option] = config.get(section, option)
            setattr(self, section, s)
