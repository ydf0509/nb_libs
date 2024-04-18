#
#
# import datetime
# from dateutil import tz
#
# #  datetime.now(tzlocal())
# # datetime.datetime(2003, 9, 27, 10, 1, 43, 673605,
# #           tzinfo=tzlocal())
# #
# # >>> datetime.now(tzlocal()).tzname()
# # 'BRST'
# #
# # >>> datetime.now(tzlocal()).astimezone(tzoffset(None, 0))
# # datetime.datetime(2003, 9, 27, 13, 3, 0, 11493,
# #           tzinfo=tzoffset(None, 0))
#
# import datetime
# print(tz.gettz().__dict__)

import datetime

# Create a datetime object in the +07:00 time zone
dt_7th = datetime.datetime(2022, 3, 1, 10, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=7)))
print(dt_7th)
print(dt_7th.strftime('%Y-%m-%d %H:%M:%S %z'))

# Adjust the time difference to the +08:00 time zone
dt_8th = dt_7th.astimezone(datetime.timezone(datetime.timedelta(hours=8)))

# Print the converted datetime object in the +08:00 time zone
print(dt_8th.strftime('%Y-%m-%d %H:%M:%S %z'))


