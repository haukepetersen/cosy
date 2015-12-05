


var db;
var chart;


var filter = function(f) {
    var xl = ['x'];
    var t = ['text'];
    var d = ['data'];
    var b = ['bss'];
    var bt = ['build time'];
    for (var i = 0; i < db.boards.length; i++) {
        var board = db.boards[i];

        if (!f || board.board.match(new RegExp(f, 'g'))) {
            xl.push(board.board);
            t.push(board.t);
            d.push(board.d);
            b.push(board.b);
            bt.push(board.buildtime);
        }
    }
    return [xl, t, d, b, bt];
}

var update = function(f) {
    chart.load({
        'columns': filter(f)
    });
}

var prepare = function() {
    chart = c3.generate({
        'bindto': '#chart',
        'size': {
            'height': 1000,
        },
        'data': {
            'x': 'x',
            'columns': filter(),
            'type': 'line',
            'colors': {
                'text': '#a173d1',
                'data': '#7b615c',
                'bss': '#de783b',
                'build time': '#35a9b5',
            },
            'axes': {
                'build time': 'y2'
              }
        },
        'bar': {
            'width': {
                'ratio': .95, // this makes bar width 50% of length between ticks
            }
        },
        'axis': {
            'x': {
                'type': 'category',
                'tick': {
                    'rotate': 90,
                    'multiline': false
                }
            },
            'y': {
                'label': {
                    'text': 'byte',
                    'position': 'outer-middle'
                }
            },
            'y2': {
                'show': true,
                'label': {
                    'text': 'ms',
                    'position': 'outer-middle'
                }
            }
        },
    });
};


d3.json("sizes.json", function(data) {
    db = data;
    d3.select("#appname").text(db.app);
    d3.select("#filter").on('input', function() {
        update(this.value);
    });
    prepare();
});
