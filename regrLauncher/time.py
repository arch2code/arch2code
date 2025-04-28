import datetime
import math

# Time delta with precision
class timedelta(datetime.timedelta):

    def __new__(cls, days=0, seconds=0, microseconds=0,
            milliseconds=0, minutes=0, hours=0, weeks=0, precision='microseconds'):

        if isinstance(precision, str):
            match precision:
                case 'seconds' : precision = 0
                case 'tenths' : precision = 1
                case 'hundredths' : precision = 2
                case 'milliseconds' : precision = 3
                case 'microseconds' : precision = 6
                case _ : precision = 6
        else:
            precision = 6

        dt_ = datetime.timedelta(days, seconds, microseconds,
            milliseconds, minutes, hours, weeks)

        microseconds_ = cls.__round_up(dt_.microseconds*1e-6, precision)
        seconds_ = int(dt_.total_seconds()) + microseconds_

        self = super().__new__(cls, 0, seconds_, 0, 0, 0, 0, 0)

        self._precision = precision

        return self

    # Read-only field accessors
    @property
    def precision(self):
        """precision"""
        return self._precision

    @staticmethod
    def __round_up(n, decimals=0):
        multiplier = 10**decimals
        return math.ceil(n * multiplier) / multiplier

    @classmethod
    def downcast(cls, baseobj, precision='microseconds'):
        return cls(0, baseobj.total_seconds(), 0, 0, 0, 0, 0, precision)

    @classmethod
    def upcast(cls, obj):
        return datetime.timedelta(0, obj.total_seconds(), 0, 0, 0, 0, 0)

    def __repr__(self):
        s = super().__repr__()
        s += " precision=%d" % self.precision
        return s

    def __str__(self):
        s = super().__str__()
        if self.microseconds:
            n = 6 - self.precision
            s = s[:-n]
        return s

