#!/usr/bin/python

import tank_temp as temperature
import datetime
import tank_relayController
import mydebug
from flask import Flask, send_file, Response, request
app = Flask(__name__)

prog = None

conf = {}
conf['relay0'] = 'relay0'
conf['relay1'] = 'relay1'
conf['relay2'] = 'relay2'
conf['relay3'] = 'relay3'

def c(n):
    s = 'relay'+str(n)
    return conf[s] != 'N'

class LogStuff(object):
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

        if '_last_changed' not in self.__dict__:
            self._last_changed = 0
            self._log = {}

    def get_temp_log(self, days):
        last_changed = temperature.log_last_changed()
        if (last_changed != self._last_changed) or (days not in self._log):
            self._last_changed = last_changed

            logdata, mn, mx = temperature.get_temp_log(days)
            new_log = []
            for e in logdata:
                fields = e.split(',')
                if len(fields) > 6:
                    new_log.append("[new Date({a}),{b}]".format(a=','.join(fields[0:5]), b=','.join(fields[5:7])))
            self._log[days] = ','.join(new_log), mn, mx
            return self._log[days]
        else:
            return self._log[days]


def gettimestamp():
    n = datetime.datetime.now()
    output = n.strftime('%d/%b %H:%M')
    return output


def graph(days=30):
    a = """
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
    google.load('visualization', '1.1', {packages: ['corechart', 'line']});
    google.setOnLoadCallback(drawChart);
    function drawChart() {
      var data = new google.visualization.DataTable();
      data.addColumn('datetime', 'Hours');
      data.addColumn('number', 'Room');
      data.addColumn('number', 'Tank');
      data.addRows([
    """

    b, mn, mx = LogStuff().get_temp_log(days)

    c = """
      ]);
      var options = {
        chartArea:{left:40,top:50},
        chart: {
          title: 'Tank verses Room Temps',
          subtitle: 'in Centigrade',
        },
        vAxis: {
          title:'degrees',
            viewWindow: {
              min: """ + str(mn) + """,
              max: """ + str(mx) + """
            },
          ticks: [""" + ','.join(map(str, range(mn, mx+1))) + """]
        },
        width: 1000,
        height: 500
      };
      var chart = new google.visualization.LineChart(document.getElementById('linechart_material'));
      chart.draw(data, options);
    }
    </script>
    """
    return a+b+c



def main_page(ctrl=False):
    line = '<a href="/all"> All </a><br>'
    line += '<a href="/month"> Month </a><br>'
    line += '<a href="/week"> Week </a><br>'
    line += '<br><div id="linechart_material"></div>'
    line += gettimestamp() + "<br><br>"
    line += temperature.get_current_temps_formatted()+"<br><br>"
    if c(0):
        line += conf['relay0']+' '+tank_relayController.get_relay_state_str(0)+"<br>"
    if c(1):
        line += conf['relay1']+' '+tank_relayController.get_relay_state_str(1)+"<br>"
    if c(2):
        line += conf['relay2']+' '+tank_relayController.get_relay_state_str(2)+"<br>"
    if c(3):
        line += conf['relay3']+' '+tank_relayController.get_relay_state_str(3)+"<br>"
    line += '<br><br>'
    if ctrl:
        if c(0):
            line += '<a href="/TR1">Toggle '+conf['relay0']+'</a></br>'
        if c(1):
            line += '<a href="/TR2">Toggle '+conf['relay1']+'</a></br>'
        if c(2):
            line += '<a href="/TR3">Toggle '+conf['relay2']+'</a></br>'
        if c(3):
            line += '<a href="/TR4">Toggle '+conf['relay3']+'</a></br>'
        line += '<br><br>'
        if c(0):
            q = tank_relayController.get_relay_query(0)
            line += '<a href="/otocinclus/setr0'+q+'">Set '+conf['relay0']+' Timings</a></br>'
        if c(1):
            q = tank_relayController.get_relay_query(1)
            line += '<a href="/otocinclus/setr1'+q+'">Set '+conf['relay1']+' Timings</a></br>'
        if c(2):
            q = tank_relayController.get_relay_query(2)
            line += '<a href="/otocinclus/setr2'+q+'">Set '+conf['relay2']+' Timings</a></br>'
        if c(3):
            q = tank_relayController.get_relay_query(3)
            line += '<a href="/otocinclus/setr3'+q+'">Set '+conf['relay3']+' Timings</a></br>'
    line += '</br>'
#    line += "Relay 3 "+tank_relayController.get_relay_state_str(2)+"<br>"
#    line += "Relay 4 "+tank_relayController.get_relay_state_str(3)+"<br><br>"
#    if ctrl:
#        line += '<a href="/TR3">Toggle Relay 3</a></br>'
#        line += '<a href="/TR4">Toggle Relay 4</a></br><br>'
#        line += '<a href="/TOR1">Override Light 1</a></br>'
#        line += '<a href="/TOR2">Override Light 2</a></br><br>'
    line += '</br>'
    line += '<br><br><a href="/LOG">Temp Log</a></br><br>'
    line += '</body>\n'
    return line


@app.route("/")
def view():
    return view_month()


@app.route("/month")
def view_month():
    line = '<html>\n<head>\n<meta http-equiv="refresh" content="30; url=/" />\n' + graph(30) + '</head>\n<body>\n'
    line += main_page()
    return line


@app.route("/week")
def view_week():
    line = '<html>\n<head>\n<meta http-equiv="refresh" content="30; url=/" />\n' + graph(7) + '</head>\n<body>\n'
    line += main_page()
    return line


@app.route("/all")
def view_all():
    line = '<html>\n<head>\n<meta http-equiv="refresh" content="30; url=/" />\n' + graph(9999) + '</head>\n<body>\n'
    line += main_page()
    return line


@app.route("/otocinclus")
def control():
    line = '<html>\n<head>\n<meta http-equiv="refresh" content="30; url=/otocinclus" />\n' \
           + graph() + '</head>\n<body>\n'
    line += main_page(True)
    return line


def setrelay(n):
    mon = request.args.get('mon')
    tue = request.args.get('tue')
    wed = request.args.get('wed')
    thu = request.args.get('thu')
    fri = request.args.get('fri')
    sat = request.args.get('sat')
    sun = request.args.get('sun')
    tank_relayController.set_schedule(n,mon,tue,wed,thu,fri,sat,sun)
    page = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Timepicker</title>
  <link rel="stylesheet" href="/static/jquery-ui.css">
  <script src="/static/jquery-1.10.2.js"></script>
  <script src="/static/jquery-ui.js"></script>
  <link rel="stylesheet" href="/static/gus1.css">
</head>
<body>
<div id="timepicker"> </div>
<div><a href="/otocinclus">BACK</a></div>
<script src="/static/gus1.js"></script>
</body>
</html>
"""
    return page

@app.route("/otocinclus/setr0")
def setr0():
    return setrelay(0)

@app.route("/otocinclus/setr1")
def setr1():
    return setrelay(1)

@app.route("/otocinclus/setr2")
def setr2():
    return setrelay(2)

@app.route("/otocinclus/setr3")
def setr3():
    return setrelay(3)

# @app.route("/TOR1")
# def toggle_override_light_1():
# #    controller.relays.get_relay(0).toggle_override()
#     return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'
#
#
# @app.route("/TOR2")
# def toggle_override_light_2():
# #    controller.relays.get_relay(1).toggle_override()
#     return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/TR1")
def toggle_light_1():
    tank_relayController.toggle_relay(0)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/TR2")
def toggle_light_2():
    tank_relayController.toggle_relay(1)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/TR3")
def toggle_light_3():
    tank_relayController.toggle_relay(2)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/TR4")
def toggle_light_4():
    tank_relayController.toggle_relay(3)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/temp")
def temp():
    send_file('/var/log/temp.txt', mimetype='text/plain')
    return view()


@app.route("/LOG")
def log():
    text, __, __ = temperature.get_temp_log(9999)
    return Response('<br>'.join(text), mimetype="text/html")


# controller = relayController.Controller()
# controller.init_timers()

if __name__ == "__main__":
    with open("main.conf") as f:
        lines = f.read().split('\n')
    for l in lines:
        l = l.strip()
        if len(l) > 0:
            f = l.split(' ')
            conf[f[0]] = ' '.join(f[1:])


    if mydebug.TEST == 0:
        app.run(host='0.0.0.0', port=5000)
    else:
        app.run(host='0.0.0.0', port=5001)
    # controller.stop()
