#!/usr/bin/python

# import os
# import tank_temp as temperature

import datetime
from flask import Flask, send_file, Response, request
import traceback

import tank
# import relay
import debug
import cfg
import logg

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

    def get_temp_log(self, days, graph_type, span):
#        key = graph_type+str(days)+'_'+str(span)

#        last_changed = logg.log_last_changed()
#        if last_changed != self._last_changed:
#            self._log = {}

#        if key not in self._log:
#            self._last_changed = last_changed

            logdata, mn, mx, sensor_names = logg.get_temp_log(days, graph_type, span)
            if mn==mx:
                if mn < 2:
                    mn = 0
                    mx = 1
            new_log = []
            for e in logdata:
                fields = e.split(',')
                if len(fields) > 1:
#                if len(fields) > 6:
                    new_log.append("[d({a}),{b}]".format(a=fields[0], b=','.join(fields[1:])))
#                    new_log.append("[new Date({a}),{b}]".format(a=','.join(fields[0:6]), b=','.join(fields[6:])))
#            self._log[key] = ','.join(new_log), mn, mx, sensor_names
            return ','.join(new_log), mn, mx, sensor_names
 #       else:
  #          return self._log[key]


def gettimestamp():
    n = datetime.datetime.now()
    output = n.strftime('%d/%b %H:%M')
    return output


def graph(days, graphobj, span):
    chart_name = 'linechart_'+graphobj.name
    b, mn, mx, sensor_names = LogStuff().get_temp_log(days, graphobj.name, span)

    a = [
        """<script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
    google.load('visualization', '1.1', {packages: ['corechart', 'line']});
    google.setOnLoadCallback(drawChart);
    function d(n){
        if (n>1000000){
            basetime = n;
            n=0;
            }
        return new Date((basetime+n)*1000);
    }
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

    scale = int(graphobj.scale)

    colours = ''
    if graphobj.graph_colours is not None:
       colours = """colors: """+graphobj.graph_colours+""","""

    c1 = """
      ]);
      var options = {
        chartArea:{left:40,top:10,width:"80%",height:"100%"},
        chart: {
          title: 'Temps',
          subtitle: 'in Centigrade'
        },
        vAxis: {
          title:'"""+str(graphobj.yaxis)+"""',
            viewWindow: {
              min: """ + str(mn) + """,
              max: """ + str(mx) + """
            },
          ticks: [""" + ','.join(map(str, range(mn, mx+1, scale))) + """]
        },
        width: 1000,
        """ + colours + """
        height: """+str(graphobj.height)+"""
      };
      var chart = new google.visualization.""" + graphobj.graph_type + """(document.getElementById('"""+chart_name+"""'));
      chart.draw(data, options);
    }
    </script>
    """
    return '\n'.join(a) + b + c1


def main_page(ctrl=False, day_count=7, span=9999):
    line  = '<a href="{cp}?d=9999&s=9999"> All </a><br>'.format(cp=current_path)
    line += '<a href="{cp}?d=30&s={s}"> Month </a><br>'.format(cp=current_path, s=span)
    line += '<a href="{cp}?d=7&s={s}"> Week </a><br>'.format(cp=current_path, s=span)
    line += '<a href="{cp}?d=1&s={s}"> Day </a><br><br>'.format(cp=current_path, s=span)

    line += '<a href="{cp}?d={d}&s=9999"> All </a><br>'.format(cp=current_path, d=day_count)
    line += '<a href="{cp}?d={d}&s=1"> 1 Day </a><br>'.format(cp=current_path, d=day_count)
    line += '<a href="{cp}?d={d}&s=2"> 2 Days </a><br>'.format(cp=current_path, d=day_count)
    line += '<a href="{cp}?d={d}&s=3"> 3 Days </a><br>'.format(cp=current_path, d=day_count)

    for chart in config.graphs_types:
        name = "linechart_{chart}".format(chart=chart)
        line += '<br><div id="{name}" style=" width:1000px;"></div>'.format(name=name)
    line += gettimestamp() + "<br><br>"

    current = logg.get_current_values_formatted()
    if 'ControlState:ACTIVE' in current:
        current_control_state = 'ACTIVE'
    else:
        current_control_state = 'OFF'

    line += current + "<br><br>"
    for relay in conf:
        line += relay['name'] + ' ' + relay.get_relay_state_str(relay['name']) + "<br>"
    line += '<br><br>'
    if ctrl:
        for relay in config.relay_items:
            line += '<a href="{cp}/TR?r={n}">Toggle {r}</a></br>'.\
                format(cp=current_path, n=relay.name, r=relay.name)
        line += '<br><br>'
        for relay in config.timer_items:
            q = tank.get_relay_query(relay.name)
            line += '<a href="{cp}/setr{q}">Set {r} Timings</a></br>'.\
                format(cp=current_path, q=q, r=relay.name)
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
    if ctrl:
        if 'OFF' in current_control_state:
            line += '<br><a href="/ON">TURN ON</a></br>'
        else:
            line += '<br><a href="/OFF">TURN OFF</a></br>'
    if ctrl:
        line += '<br><a href="/otocinclus/configure">configure</a></br>'
    line += '</body>\n'
    return line


def view(ctrl=False):
    line = ''
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

        try:
            span = int(request.args.get('s'))
        except (ValueError, TypeError):
            span = 99999

        charts = []
        for g in config.graph_items:
            q = graph(day_count, g, span)
            charts.append(q)

            #
            # for gt cfg.graphs_items:
            #     if gt[tank_cfg.ITEM_GRAPH] == gt:

        line = '<html>\n<head>\n<meta http-equiv="refresh" content="30; url={cp}" />\n</head>\n<body>{graph}\n'.\
            format(cp=current_path, graph=' '.join(charts))
        line += main_page(ctrl, day_count, span)
    except Exception as e:
        print e
        print traceback.format_exc()
    return line


@app.route("/")
def rootview():
    global current_path
    current_path = '/'
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
    tank.set_schedule(relay_name, mon, tue, wed, thu, fri, sat, sun)
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
    tank.toggle_relay(relay_name)
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
    text, __, __, __ = logg.get_temp_log(9999, None)
    return Response('<br>'.join(text), mimetype="text/html")


@app.route("/OFF")
def turn_off():
    config.control_state = 'OFF'
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/ON")
def turn_on():
    config.control_state = 'ACTIVE'
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/otocinclus" />\n</head>\n<body></<body>\n'


@app.route("/otocinclus/configure", methods=['GET'])
def configure_view():
    o = ['<!DOCTYPE html><html lang="en"><body><form action="." method="POST">']

    for section, values in config.configurable_items:
        vals = str.split(values, ',')
        name = cfg.Config().config.get(section, 'name')
        o.append("<h1>{t}</h1>".format(t=name))
        for v in vals:
            n = "{s}_{v}".format(s=section, v=v)
            o.append('{f}: <input type="text" name="{name}" value="{v}"><br>'.
                     format(f=v, name=n, v=cfg.Config().config.get(section, v)))

    o.append('<input type="submit" name="my-form" value="Send">')
    o.append("""</form></body></html>""")
    return ''.join(o)


@app.route('/otocinclus/', methods=['POST'])
def my_form_post():
    data = []
    for section, values in config.configurable_items:
        vals = str.split(values, ',')
        for v in vals:
            n = "{s}_{v}".format(s=section, v=v)
            new_value = request.form[n]
            data.append((section, v, new_value))
    config.set_config_data(data)
    return view(True)

if __name__ == "__main__":
        config = cfg.Config()

        graphs = config.graphs_types
        graphed = config.graphed_items

        if debug.TEST == 0:
            app.run(host='0.0.0.0', port=5000)
        else:
            app.run(host='0.0.0.0', port=5001)
