#!/usr/bin/python

import temp as temperature
#import timer
import datetime
import relayController

from flask import Flask, send_file, Response
app = Flask(__name__)

prog = None


def gettimestamp():
    n = datetime.datetime.now()
    output = n.strftime('%d/%b %H:%M')
    return output


def graph():
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
      data.addRows(["""

    b = tmp.get_log2()

    c = """]);
      var options = {
chartArea:{left:40,top:50},
        chart: {
          title: 'Tank verses Room Temps',
          subtitle: 'in Centigrade',
                },

vAxis: {
title:'degrees',
    viewWindow: {
        min: 18,
        max: 30
    },
    ticks: [18,19,20,21,22,23,24,25,26,27,28,29,30] 
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
#      data.addColumn('number', 'Tank');
#      data.addColumn({type: 'string', role: 'tooltip'});


@app.route("/")
def view():
    line = '<html>\n<head>\n<meta http-equiv="refresh" content="30; url=/" />\n' + graph() + '</head>\n<body>\n'
    line += '<div id="linechart_material"></div>'
    line += gettimestamp() + "<br><br>"
    line += tmp.get_all()+"<br><br>"
    line += "Light 1 "+controller.get_relay_state_str(0)+"<br>"
    line += "Light 2 "+controller.get_relay_state_str(1)+"<br><br>"
    line += '</br>'
    line += "Relay 3 "+controller.get_relay_state_str(2)+"<br>"
    line += "Relay 4 "+controller.get_relay_state_str(3)+"<br><br>"
    line += '</br>'
    line += '<br><br><a href="/LOG">Temp Log</a></br><br>'
    line += '</body>\n'
    return line


@app.route("/otocinclus")
def control():
    line = '<html>\n<head>\n<meta http-equiv="refresh" content="30; url=/otocinclus" />\n' \
           + graph() + '</head>\n<body>\n'
    line += '<div id="linechart_material"></div>'
    line += gettimestamp() + "<br><br>"
    line += tmp.get_all()+"<br><br>"
    line += "Light 1 "+controller.get_relay_state_str(0)+"<br>"
    line += "Light 2 "+controller.get_relay_state_str(1)+"<br><br>"
    line += '<a href="/TR1">Toggle Light 1</a></br>'
    line += '<a href="/TR2">Toggle Light 2</a></br><br>'
    line += "Relay 3 "+controller.get_relay_state_str(2)+"<br>"
    line += "Relay 4 "+controller.get_relay_state_str(3)+"<br><br>"
    line += '<a href="/TR3">Toggle Relay 3</a></br>'
    line += '<a href="/TR4">Toggle Relay 4</a></br><br>'
    line += '<a href="/TOR1">Override Light 1</a></br>'
    line += '<a href="/TOR2">Override Light 2</a></br><br>'
    line += '<br><br><a href="/LOG">Temp Log</a></br><br>'

    line += '</body>\n'
    return line


@app.route("/TOR1")
def toggle_override_light_1():
    controller.relays.get_relay(0).toggle_override()
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/" />\n</head>\n<body></<body>\n'


@app.route("/TOR2")
def toggle_override_light_2():
    controller.relays.get_relay(1).toggle_override()
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/" />\n</head>\n<body></<body>\n'


@app.route("/TR1")
def toggle_light_1():
    controller.toggle(0)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/" />\n</head>\n<body></<body>\n'


@app.route("/TR2")
def toggle_light_2():
    controller.toggle(1)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/" />\n</head>\n<body></<body>\n'


@app.route("/TR3")
def toggle_light_3():
    controller.toggle(2)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/" />\n</head>\n<body></<body>\n'


@app.route("/TR4")
def toggle_light_4():
    controller.toggle(3)
    return '<html>\n<head>\n<meta http-equiv="refresh" content="0; url=/" />\n</head>\n<body></<body>\n'


@app.route("/temp")
def temp():
    send_file('/var/log/temp.txt', mimetype='text/plain')
    return view()


@app.route("/LOG")
def temp():
    text = tmp.get_log().replace("\n", "<br>")
    return Response(text, mimetype="text/html")


controller = relayController.Controller()
controller.init_timers()

tmp = temperature.Temp()
tmp.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0')
    tmp.stop()
    controller.stop()
