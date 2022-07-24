
SEND ON drone/dctrl PAYLOAD 
{"operation":"GOTO","d_lat":"35.887095440363034","d_lon":"139.94183063507083","d_alt":"30.0"}









#############################################################




1
{u'sfx': u"'QGC WPL 110'+'\r\n'", 
u'wp4': u'4\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n', 
u'wp5': u'5\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n', 
u'wp6': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n', 
u'wp0': u'0\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n', 
u'wp1': u'1\t0\t0\t22\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n', 
u'wp2': u'2\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n', 
u'wp3': u'3\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n', 
u'operation': u'MISSION'}
3
4




[
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}
]



1
[{u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}, {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.89\t139.95\t30\t1\r\n'}]
3
4
Exception in thread Thread-2:
Traceback (most recent call last):
  File "/usr/lib/python2.7/threading.py", line 801, in __bootstrap_inner
    self.run()
  File "/usr/lib/python2.7/threading.py", line 754, in run
    self.__target(*self.__args, **self.__kwargs)
  File "/home/sayz/.local/lib/python2.7/site-packages/paho/mqtt/client.py", line 3591, in _thread_main
    self.loop_forever(retry_first_connection=True)
  File "/home/sayz/.local/lib/python2.7/site-packages/paho/mqtt/client.py", line 1756, in loop_forever
    rc = self._loop(timeout)
  File "/home/sayz/.local/lib/python2.7/site-packages/paho/mqtt/client.py", line 1164, in _loop
    rc = self.loop_read()
  File "/home/sayz/.local/lib/python2.7/site-packages/paho/mqtt/client.py", line 1556, in loop_read
    rc = self._packet_read()
  File "/home/sayz/.local/lib/python2.7/site-packages/paho/mqtt/client.py", line 2439, in _packet_read
    rc = self._packet_handle()
  File "/home/sayz/.local/lib/python2.7/site-packages/paho/mqtt/client.py", line 3033, in _packet_handle
    return self._handle_publish()
  File "/home/sayz/.local/lib/python2.7/site-packages/paho/mqtt/client.py", line 3327, in _handle_publish
    self._handle_on_message(message)
  File "/home/sayz/.local/lib/python2.7/site-packages/paho/mqtt/client.py", line 3570, in _handle_on_message
    on_message(self, self._userdata, message)
  File "/home/sayz/vscrepo/drone_ctrl/dctrl/script/mqtt_cls.py", line 220, in on_message_m
    self.drone_mission["operation"] = recvData["operation"]
TypeError: list indices must be integers, not str




1
[{
    u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", 
    u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.88483543074129\t35.88483543074129\t30\t1\r\n'}, 
    {
        u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", 
    u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.88483543074129\t35.88483543074129\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", 
    u'wp': u'6\t0\t0\t16\t0\t0\t0\t0\t35.88483543074129\t35.88483543074129\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': 
    u'6\t0\t0\t16\t0\t0\t0\t0\t35.88483543074129\t35.88483543074129\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': 
    u'6\t0\t0\t16\t0\t0\t0\t0\t35.88483543074129\t35.88483543074129\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': 
    u'6\t0\t0\t16\t0\t0\t0\t0\t35.88483543074129\t35.88483543074129\t30\t1\r\n'}, 
    {u'operation': u'MISSION', u'sfx': u"'QGC WPL 110'+'\r\n'", u'wp': 
    u'6\t0\t0\t16\t0\t0\t0\t0\t35.88483543074129\t35.88483543074129\t30\t1\r\n'}]
3
4













