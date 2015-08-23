#!/usr/bin/python

import os
import tank_temp as temperature
import datetime
import tank_relayController
import mydebug
from flask import Flask, send_file, Response, request
import tank_cfg
import traceback

app = Flask(__name__)

prog = None
conf = []
prev_count = 30
current_path = '/'


def c(n):
    return n < len(conf)


class LogStuff(object):
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

        if '_last_changed' not in self.__dict__:
            self._last_changed = 0
            self._log = {}

    def get_temp_log(self, days, graph_type):

        last_changed = temperature.log_last_changed()
#        if (last_changed != self._last_changed) or (days not in self._log):
        if True:
            self._last_changed = last_changed

            logdata, mn, mx, sensor_names = temperature.get_temp_log(days, graph_type)
            new_log = []
            for e in logdata:
                fields = e.split(',')
                if len(fields) > 6:
                    new_log.append("[new Date({a}),{b}]".format(a=','.join(fields[0:5]), b=','.join(fields[5:])))
            self._log[days] = ','.join(new_log), mn, mx, sensor_names
            return self._log[days]
        else:
            return self._log[days]


def gettimestamp():
    n = datetime.datetime.now()
    output = n.strftime('%d/%b %H:%M')
    return output


def graph(days=30, graph_type='temps'):
    chart_name = 'linechart_'+graph_type
    b, mn, mx, sensor_names = LogStuff().get_temp_log(days, graph_type)

    a = [
        """<script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
    google.load('visualization', '1.1', {packages: ['corechart', 'line']});
    google.setOnLoadCallback(drawChart);
    function drawChart() {
      var data = new google.visualization.DataTable();
      data.addColumn('datetime', 'Hours');
    """
    ]

    # a.append("""
    # <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    # <script type="text/javascript">
    # google.load('visualization', '1.1', {packages: ['corechart', 'line']});
    # google.setOnLoadCallback(drawChart);
    # function drawChart() {
    #   var data = new google.visualization.DataTable();
    #   data.addColumn('datetime', 'Hours');
    # """)

    for name in sensor_names:
        a.append("data.addColumn('number', '{name}');".format(name=name))
    a.append("data.addRows([")

    c1 = """
      ]);
      var options = {
        chartArea:{left:40,top:50},
        chart: {
          title: 'Temps',
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
      var chart = new google.visualization.LineChart(document.getElementById('"""+chart_name+"""'));
      chart.draw(data, options);
    }
    </script>
    """
    return '\n'.join(a) + b + c1


def main_page(ctrl=False):
    line = '<a href="{cp}?d=9999"> All </a><br>'.format(cp=current_path)
    line += '<a href="{cp}?d=30"> Month </a><br>'.format(cp=current_path)
    line += '<a href="{cp}?d=7"> Week </a><br>'.format(cp=current_path)
    line += '<a href="{cp}?d=1"> Day </a><br>'.format(cp=current_path)
    for chart in cfg.graphs_types:
        name = "linechart_{chart}".format(chart=chart)
        line += '<br><div id="{name}"></div>'.format(name=name)
    line += gettimestamp() + "<br><br>"
    line += temperature.get_current_temps_formatted()+"<br><br>"
    for relay in conf:
        line += relay['name'] + ' ' + tank_relayController.get_relay_state_str(relay['name']) + "<br>"
    line += '<br><br>'
    if ctrl:
        for relay in conf:
            line += '<a href="{cp}/TR?r={n}">Toggle {r}</a></br>'.\
                format(cp=current_path, n=relay['name'], r=relay['name'])
        line += '<br><br>'
        for relay in conf:
            q = tank_relayController.get_relay_query(relay['name'])
            line += '<a href="{cp}/setr{q}">Set {r} Timings</a></br>'.\
                format(cp=current_path, q=q, r=relay['name'])
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


def view(ctrl=False):
    try:
        global prev_count
        try:
            day_count = int(request.args.get('d'))
        except (ValueError, TypeError):
            day_count = None
        if day_count is None:
            if prev_count is not None:
                day_count = prev_count
            else:
                day_count = 30
        prev_count = day_count

        charts = []
        for gt in cfg.graphs_types:
            q = graph(day_count, gt)
            charts.append(q)


            #
            # for gt cfg.graphs_items:
            #     if gt[tank_cfg.ITEM_GRAPH] == gt:

        line = '<html>\n<head>\n<meta http-equiv="refresh" content="30; url={cp}" />\n{graph}</head>\n<body>\n'.\
            format(cp=current_path, graph=' '.join(charts))
        line += main_page(ctrl)
    except Exception as e:
        print e
        print traceback.format_exc()
    return line


@app.route("/")
def rootview():
    return view(False)
    # global prev_count
    # try:
    #     day_count = int(request.args.get('d'))
    # except (ValueError, TypeError):
    #     day_count = None
    # if day_count is None:
    #     if prev_count is not None:
    #         day_count = prev_count
    #     else:
    #         day_count = 30
    # prev_count = day_count
    # line = '<html>\n<head>\n<meta http-equiv="refresh" content="30; url=/" />\n' + \
    #        graph(day_count) + '</head>\n<body>\n'
    # line += main_page()
    # return line


@app.route("/otocinclus")
def control():
    global current_path
    current_path = '/otocinclus'
    return view(True)
    # line = '<html>\n<head>\n<meta http-equiv="refresh" content="30; url=/otocinclus" />\n' \
    #        + graph() + '</head>\n<body>\n'
    # line += main_page(True)
    # return line


@app.route("/otocinclus/setr")
def setrelay():
    relay_name = request.args.get('r')
    mon = request.args.get('mon')
    tue = request.args.get('tue')
    wed = request.args.get('wed')
    thu = request.args.get('thu')
    fri = request.args.get('fri')
    sat = request.args.get('sat')
    sun = request.args.get('sun')
    tank_relayController.set_schedule(relay_name, mon, tue, wed, thu, fri, sat, sun)
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


#
# def setr():
#     return setrelay()


# @app.route("/otocinclus/setr0")
# def setr0():
#     return setrelay(0)
#
#
# @app.route("/otocinclus/setr1")
# def setr1():
#     return setrelay(1)
#
#
# @app.route("/otocinclus/setr2")
# def setr2():
#     return setrelay(2)
#
#
# @app.route("/otocinclus/setr3")
# def setr3():
#     return setrelay(3)

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

@app.route("/otocinclus/TR")
def toggle_relay():
    relay_name = request.args.get('r')
    print relay_name
    tank_relayController.toggle_relay(relay_name)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


# @app.route("/TR0")
# def toggle_light_1():
#     tank_relayController.toggle_relay(0)
#     return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'
#
#
# @app.route("/TR0")
# def toggle_light_1():
#     tank_relayController.toggle_relay(0)
#     return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'
#
#
# @app.route("/TR1")
# def toggle_light_2():
#     tank_relayController.toggle_relay(1)
#     return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'
#
#
# @app.route("/TR2")
# def toggle_light_3():
#     tank_relayController.toggle_relay(2)
#     return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'
#
#
# @app.route("/TR3")
# def toggle_light_4():
#     tank_relayController.toggle_relay(3)
#     return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'
#

@app.route("/temp")
def temp():
    send_file('/var/log/temp.txt', mimetype='text/plain')
    return view()


@app.route("/LOG")
def log():
    text, __, __, __ = temperature.get_temp_log(9999)
    return Response('<br>'.join(text), mimetype="text/html")


# controller = relayController.Controller()
# controller.init_timers()

if __name__ == "__main__":
#    try:
        cfg = tank_cfg.Config()

        graphs = cfg.graphs_types
        graphed = cfg.graphs_items
        #
        # for r in cfg.items:
        #     if r[tank_cfg.ITEM_TYPE] == tank_cfg.TIMER_TYPE:
        #         conf.append(r)
        #
        # for r in cfg.items:
        #     if r[tank_cfg.ITEM_TYPE] == tank_cfg.TIMER_TYPE:
        #         conf.append(r)


        # for l in lines:
        #     l = l.strip()
        #     if len(l) > 0:
        #         f = l.split(' ')
        #         conf[f[0]] = ' '.join(f[1:])

        if mydebug.TEST == 0:
            app.run(host='0.0.0.0', port=5000)
        else:
            app.run(host='0.0.0.0', port=5001)
    # except IOError:
    #     print "Could not read 'main.conf' config file"

    # controller.stop()
