#!/usr/bin/python

import temp as temperature
import datetime
import relayController

from flask import Flask, send_file, Response
app = Flask(__name__)

prog = None


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
    line += "Light 1 "+controller.get_relay_state_str(0)+"<br>"
    line += "Light 2 "+controller.get_relay_state_str(1)+"<br><br>"
    if ctrl:
        line += '<a href="/TR1">Toggle Light 1</a></br>'
        line += '<a href="/TR2">Toggle Light 2</a></br><br>'
    line += '</br>'
    line += "Relay 3 "+controller.get_relay_state_str(2)+"<br>"
    line += "Relay 4 "+controller.get_relay_state_str(3)+"<br><br>"
    if ctrl:
        line += '<a href="/TR3">Toggle Relay 3</a></br>'
        line += '<a href="/TR4">Toggle Relay 4</a></br><br>'
        line += '<a href="/TOR1">Override Light 1</a></br>'
        line += '<a href="/TOR2">Override Light 2</a></br><br>'
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


@app.route("/TOR1")
def toggle_override_light_1():
    controller.relays.get_relay(0).toggle_override()
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/TOR2")
def toggle_override_light_2():
    controller.relays.get_relay(1).toggle_override()
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/TR1")
def toggle_light_1():
    controller.toggle(0)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/TR2")
def toggle_light_2():
    controller.toggle(1)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/TR3")
def toggle_light_3():
    controller.toggle(2)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/TR4")
def toggle_light_4():
    controller.toggle(3)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/temp")
def temp():
    send_file('/var/log/temp.txt', mimetype='text/plain')
    return view()


@app.route("/LOG")
def log():
    text, __, __ = temperature.get_temp_log(9999)
    return Response('<br>'.join(text), mimetype="text/html")


controller = relayController.Controller()
controller.init_timers()

# tmp = temperature.Temp()
# tmp.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0')
#    tmp.stop()
    controller.stop()
