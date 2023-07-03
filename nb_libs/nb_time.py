import copy
import typing
import re
import time
import datetime
import pytz
from tzlocal import get_localzone


class DatetimeConverter:
    """ 时间转换，支持链式操作，纯面向对象的的。

    相比模块级下面定义几十个函数，然后将不同类型的时间变量传到不同的函数中return结果，然后把结果作为入参传入到另一个函数进行转换，
    纯面向对象支持链式转换的要方便很多。

    初始化能够接受的变量类型丰富，可以传入一切类型的时间变量。

    """
    DATETIME_FORMATTER = "%Y-%m-%d %H:%M:%S %z"  # 2023-07-03 16:20:21 +0800 ,带时区的可以正确转化到时间戳，没有带时区的字符串，在strptime时候，无法准确转化到时区。
    DATETIME_FORMATTER_NO_ZONE = "%Y-%m-%d %H:%M:%S"
    DATETIME_FORMATTER2 = "%Y-%m-%d"
    DATETIME_FORMATTER3 = "%H:%M:%S"

    def __init__(self, datetimex: typing.Union[None, int, float, datetime.datetime, str, 'DatetimeConverter'] = None,
                 datetime_formatter=DATETIME_FORMATTER,
                 time_zone: str = get_localzone().zone):
        """
        :param datetimex: 接受时间戳  datatime类型 和 时间字符串 和类对象本身四种类型,如果为None，则默认当前时间。
        :param time_zone   时区例如 Asia/Shanghai， UTC  UTC+8  GMT+8 等。
        """
        init_params = copy.copy(locals())
        init_params.pop('self')
        init_params.pop('datetimex')
        self.init_params = init_params

        self.time_zone_str = time_zone

        '''
        将 time_zone 转成 pytz 可以识别的对应时区
        '''

        self.time_zone_obj = self.build_pytz_timezone(time_zone)
        self.datetime_formatter = datetime_formatter

        if isinstance(datetimex, str):
            self.datetime_obj = datetime.datetime.strptime(datetimex, self.datetime_formatter)
        elif isinstance(datetimex, (int, float)):
            if datetimex < 1:
                datetimex += 86400
            self.datetime_obj = datetime.datetime.fromtimestamp(datetimex, tz=self.time_zone_obj)  # 时间戳0在windows会出错。
        elif isinstance(datetimex, datetime.datetime):
            self.datetime_obj = datetimex
        elif isinstance(datetimex, DatetimeConverter):
            self.datetime_obj = datetimex.datetime_obj
        elif datetimex is None:
            self.datetime_obj = datetime.datetime.now(tz=self.time_zone_obj)
        else:
            raise ValueError('实例化时候的传参不符合规定')

    @staticmethod
    def build_pytz_timezone(time_zone: str):
        # UTC 负时区对应的 pytz 可以识别的时区
        burden_timezone = 'Etc/GMT+'
        # UTC 正时区对应的 pytz 可以识别的时区
        just_timezone = 'Etc/GMT-'
        # 截取 UTC 时区差值,eg:zone_code=UTC+5,count=5
        count = time_zone[-1]
        if '-' in time_zone:  # 就是这样没有反。
            pytz_timezone = pytz.timezone(burden_timezone + count)
        elif '+' in time_zone:
            pytz_timezone = pytz.timezone(just_timezone + count)
        else:
            pytz_timezone = pytz.timezone(time_zone)
        return pytz_timezone

    @property
    def datetime_str(self) -> str:
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER)

    @property
    def time_str(self) -> str:
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER3)

    @property
    def date_str(self) -> str:
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER2)

    def get_str_by_specify_formatter(self, specify_formatter='%Y-%m-%d %H:%M:%S'):
        return self.datetime_obj.strftime(specify_formatter)

    @property
    def timestamp(self) -> float:
        return self.datetime_obj.timestamp()

    def is_greater_than_now(self) -> bool:
        return self.timestamp > time.time()

    def __str__(self) -> str:
        return self.datetime_str

    def __call__(self) -> datetime.datetime:
        return self.datetime_obj

    # 以下为不常用的辅助方法。
    def get_converter_by_interval_seconds(self, seconds_interval) -> 'DatetimeConverter':
        return self.__class__(self.datetime_obj + datetime.timedelta(seconds=seconds_interval),
                              **self.init_params)

    def get_converter_by_interval_minutes(self, minutes_interval) -> 'DatetimeConverter':
        return self.__class__(self.datetime_obj + datetime.timedelta(seconds=minutes_interval),
                              **self.init_params)

    def get_converter_by_interval_hour(self, hour_interval) -> 'DatetimeConverter':
        return self.__class__(self.datetime_obj + datetime.timedelta(hours=hour_interval), **self.init_params)

    def get_converter_by_interval_days(self, days_interval) -> 'DatetimeConverter':
        return self.__class__(self.datetime_obj + datetime.timedelta(days=days_interval), **self.init_params)

    @property
    def one_hour_ago_converter(self) -> 'DatetimeConverter':
        """
        酒店经常需要提前一小时免费取消，直接封装在这里
        :return:
        """
        one_hour_ago_datetime_obj = self.datetime_obj + datetime.timedelta(hours=-1)
        return self.__class__(one_hour_ago_datetime_obj, **self.init_params)

    @property
    def one_day_ago_converter(self) -> 'DatetimeConverter':
        one_hour_ago_datetime_obj = self.datetime_obj + datetime.timedelta(days=-1)
        return self.__class__(one_hour_ago_datetime_obj, **self.init_params)

    @property
    def next_day_converter(self) -> 'DatetimeConverter':
        one_hour_ago_datetime_obj = self.datetime_obj + datetime.timedelta(days=1)
        return self.__class__(one_hour_ago_datetime_obj, **self.init_params)

    @property
    def today_zero_timestamp(self):
        # zero_ts = time.mktime(datetime.date.today().timetuple())
        # return zero_ts
        now = datetime.datetime.now()

        # 创建(对应的)时区对象
        tz = self.build_pytz_timezone(self.time_zone_str)

        # 获取当天零点时间
        today_start = tz.localize(datetime.datetime(now.year, now.month, now.day, 0, 0, 0))

        # 将当天零点时间转换为时间戳
        timestamp = int(today_start.timestamp())

        return timestamp


def seconds_to_hour_minute_second(seconds):
    """
    把秒转化成还需要的时间
    :param seconds:
    :return:
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


if __name__ == '__main__':
    import nb_log

    """
    1557113661.0
    '2019-05-06 12:34:21'
    '2019/05/06 12:34:21'
    DatetimeConverter(1557113661.0)()
    """
    # noinspection PyShadowingBuiltins
    # o3 = DatetimeConverter('2019-05-06 12:34:21')
    # print(DatetimeConverter(o3))
    # print(o3)
    # print(o3.next_day_converter.next_day_converter.next_day_converter)  # 可以无限链式。
    # print('- - - - -  - - -')
    # o = DatetimeConverter()
    # print(o)
    # print(o.get_str_by_specify_formatter('%Y %m %dT%H:%M:%S'))
    # print(o.date_str)
    # print(o.timestamp)
    # print('***************')
    # o2 = o.one_hour_ago_converter
    # print(o2)
    # print(o2.date_str)
    # print(o2.timestamp)
    # print(o2.is_greater_than_now())
    # print(o2(), type(o2()))
    # print(DatetimeConverter())
    # print(datetime.datetime.now())
    # time.sleep(1)
    # print(DatetimeConverter())
    # print(datetime.datetime.now())
    # print(DatetimeConverter(3600 * 24))
    #
    # print(seconds_to_hour_minute_second(3600 * 2.3))
    #
    # print(DatetimeConverter('2019-05-06 12:34:21').one_hour_ago_converter.one_hour_ago_converter)
    # print(DatetimeConverter(
    #     1596985665).one_hour_ago_converter.one_hour_ago_converter)
    # print(DatetimeConverter(
    #     datetime.datetime(year=2020, month=5, day=4)).one_hour_ago_converter.one_hour_ago_converter)

    print(DatetimeConverter())

    default_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    print(default_tz)

    from tzlocal import get_localzone

    local_tz = get_localzone()

    print(local_tz)

    print(DatetimeConverter(time_zone='UTC+8').today_zero_timestamp)
