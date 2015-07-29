var params = {};


var orig_query = location.search;

if (location.search) {
    var parts = location.search.substring(1).split('&');

    for (var i = 0; i < parts.length; i++) {
        var nv = parts[i].split('=');
        if (!nv[0]) continue;
        params[nv[0]] = nv[1] || true;
    }
}

window.onload = function () {
    create_timepicker()
};

function gethoursetting(s, n) {
    var num = parseInt(s);
    for (var i = 1; i < n; i++) {
        num = Math.floor(num / 2)
    }
    var r = num & 1;
    return (r > 0);
}

function getday(i) {
    var days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    return days[i];
}

function gettime(i) {
    return pad(Math.floor(i / 2), 2) + ":" + pad((i % 2) * 30, 2)
}

function gethour(i) {
    var n = Math.floor(i / 2);
    if ((n * 2) == i) {
        var suffix = "";
        if (n == 0) {
            suffix = "am";
        } else {
            if (n == 12) {
                suffix = "pm";
            }
        }
        return "" + n + suffix
    } else {
        return ""
    }
}

function pad(num, size) {
    var s = "000000000" + num;
    return s.substr(s.length - size);
}

function get_param(name) {
    var ret = 0;
    if (undefined != params[name]) {
        ret = parseInt(params[name], 16);
    }
    return ret;
}

function create_timepicker() {
    var monday = get_param('mon');
    var tuesday = get_param('tue');
    var wednesday = get_param('wed');
    var thursday = get_param('thu');
    var friday = get_param('fri');
    var saturday = get_param('sat');
    var sunday = get_param('sun');

    var a = '<div id="tp1">' +
        '<p class="hourinfo" data-Monday=' + monday.toString(16) + '>Monday = 0 hours</p>' +
        '<p class="hourinfo" data-Tuesday=' + tuesday.toString(16) + '>Tuesday = 0 hours</p>' +
        '<p class="hourinfo" data-Wednesday=' + wednesday.toString(16) + '>Wednesday = 0 hours</p>' +
        '<p class="hourinfo" data-Thursday=' + thursday.toString(16) + '>Thursday = 0 hours</p>' +
        '<p class="hourinfo" data-Friday=' + friday.toString(16) + '>Friday = 0 hours</p>' +
        '<p class="hourinfo" data-Saturday=' + saturday.toString(16) + '>Saturday = 0 hours</p>' +
        '<p class="hourinfo" data-Sunday=' + sunday.toString(16) + '>Sunday = 0 hours</p><br>' +
        '</div>';

    var timepicker = $("#timepicker");

    // timepicker.append(a);


    var spacer = '<li class="legend_hour"></li>';

    var content = '' + spacer;

    for (var i = 0; i < 48; i++) {
        var hour = '<li class="legend_hour">' + gethour(i) + '</li>';
        content = content.concat(hour);
    }
    var legend = '<div><ul id="legend" class="legend_day">' + content + '</ul></div>';

    var week = "" + legend;


    for (var d = 0; d < 7; d++) {
        var num = 0;
        if (d == 0) {
            num = monday;
        }
        if (d == 1) {
            num = tuesday;
        }
        if (d == 2) {
            num = wednesday;
        }
        if (d == 3) {
            num = thursday;
        }
        if (d == 4) {
            num = friday;
        }
        if (d == 5) {
            num = saturday;
        }
        if (d == 6) {
            num = sunday;
        }


        var title = '<li class="title"  data-tag="0">' + getday(d) + '</li>';
//        var total = '<li class="total" data-tag="total">00</li>';
        content = "" + title;
        for (i = 1; i < 49; i++) {
//            var tt = "'" + gettime(i) + "'";
            var cls = "hour ui-selectee";
            if (gethoursetting(num, i)) {
                cls = cls + " ui-selected";
            }
//            hour = '<li class="' + cls + '" title=' + tt + '></li>';
            hour = '<li class="' + cls + '"></li>';
            content = content.concat(hour);
        }


        //'<p class="hourinfo" data-Monday='+monday.toString(16)+'>Monday = 0 hours</p>' +


        hour = '<li class="hourinfo" data-' + getday(d) + '="' + get_param(getday(d)) + '">' + '0' + '</li>';
        content = content.concat(hour);

        var day = '<div><ul id="selectable" class="day' + d + ' day ui-selectable">' + content + '</ul></div>';

        week = week.concat(day)
    }

    timepicker.append('<div><div id="tp0" style="display: block;">' + week + '</div></div>');

    timepicker.append('<div id="tp2"><a id="save_settings"  style="display: block;" href="/"><br><a id="revert_settings"  style="display: block;" href="/"></a></div></div>');

    var updateAllTimesInterval = setInterval(function () {
        update_all_times()
    }, 10);

    function update_all_times() {
        clearInterval(updateAllTimesInterval);
        update_time_disp($(".day0")[0]);
        update_time_disp($(".day1")[0]);
        update_time_disp($(".day2")[0]);
        update_time_disp($(".day3")[0]);
        update_time_disp($(".day4")[0]);
        update_time_disp($(".day5")[0]);
        update_time_disp($(".day6")[0]);
        update_query();
    }

    function get_day_value(day) {
        var s1 = ("data-" + day).toLowerCase();
        var s = ("[" + s1 + "]");
        var x = $(s, $(document));
        return x[0].getAttribute(s1).toString();
    }

    //function set_day_value(day, bitmask, hours) {
    //    var s1 = ("data-" + day).toLowerCase();
    //    var s = ("[" + s1 + "]");
    //    var x = $(s, $(document));
    //    x[0].textContent = hours + ' hours';
    //    return x[0].setAttribute(s1, bitmask.toString(16));
    //}


    function update_query() {
        var query =
            '?mon=' + get_day_value('monday') +
            '&tue=' + get_day_value('tuesday') +
            '&wed=' + get_day_value('wednesday') +
            '&thu=' + get_day_value('thursday') +
            '&fri=' + get_day_value('friday') +
            '&sat=' + get_day_value('saturday') +
            '&sun=' + get_day_value('sunday');

        if (query != orig_query) {
            var savesettings = document.getElementById("save_settings");
            savesettings.href = location.pathname + query;
            savesettings.textContent = "SAVE SETTINGS";

            var revertsettings = document.getElementById("revert_settings");
            revertsettings.href = location.pathname + orig_query;
            revertsettings.textContent = "REVERT CHANGES";

        }
    }


    function update_time_disp(element) {
        var prev = null;
        var t = 0;
        var q = 1;
        var first = null;
        var children = element.children;
        var title = '';
        var hours = 0;
        for (var i = 0, c = 0; i < children.length; i++) {
            var child = children[i];
            if (child.classList.contains('title')) {
                title = child.textContent
            }
            if (child.classList.contains('hour')) {
                if (child.classList.contains('ui-selected')) {
                    hours += 0.5;
                    t = t + q;
                    if (first == null) {
                        child.textContent = gettime(c);
                        first = child
                    } else {
                        child.textContent = ""
                    }
                }
                else {
                    if (first != null) {
                        var txt = first.textContent + " - " + gettime(c);
                        first.textContent = txt;
                        prev.textContent = txt;
                    }
                    first = null;
                    child.textContent = ""
                }
                q = q * 2;
                c += 1
            }
            prev = child
        }
        if (first != null) {
            txt = first.textContent + " - " + gettime(c);
            first.textContent = txt;
            prev.textContent = txt;
        }
        var s1 = ("data-" + title).toLowerCase();
        child.textContent = hours + ' hours';
        child.setAttribute(s1, t.toString(16));
    }


    $(function () {
        //noinspection JSUnresolvedFunction
        $(document).tooltip();
    });

    $(function () {
        //noinspection JSUnresolvedFunction
        $("ul.ui-selectable").selectable({
            stop: function (event, ui) {
                if (event) {
                }
                if (ui) {
                }
                update_time_disp(this);
                update_query();
            }
        });

    });

}
