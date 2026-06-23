$win.on('load', function(){
	if (!$('#visitor-week-chart')[0]) {
		return;
	}
	var _chartVisitorWeek = new Chartist.Bar('#visitor-week-chart', {
				labels: labelsWeeksLogins,
				series: [
					seriesWeeksLogins,
				]
			}, {
			axisY: {
				/*labelInterpolationFnc: function (value) {
                    return (value / 1000) + 'k';
                },*/
                scaleMinSpace: 20,
                showGrid: true,
				onlyInteger: true,
            },
            axisX: {
                showGrid: false
            },
            plugins: [
                Chartist.plugins.tooltip({
                    appendToBody: false,
                    pointClass: 'ct-point'
                })
            ],
	})

	_chartVisitorWeek.on('draw', function (data) {
            if (data.type === 'bar') {
				var attr={
					style: 'stroke-width: 24px',
					y1: 307,
					x1: data.x1 + 0.001
				};
				if (data.y2 > 292) {
					attr['y2'] = 302;
				}
				data.element.attr(attr);

				if (data.y2 < 292) {
					data.group.append(new Chartist.Svg('circle', {
						cx: data.x2,
						cy: data.y2,
						r: 12
					}, 'ct-slice-pie'));
				}
            }
    });

	_chartVisitorWeek.on('created', function (data) {
            var defs = data.svg.querySelector('defs') || data.svg.elem('defs');
            defs.elem('linearGradient', {
                id: 'barGradient2',
                x1: 0,
                y1: 0,
                x2: 0,
                y2: 1
            }).elem('stop', {
                offset: '10%',
                'stop-color': 'rgba(249,111,155,0.9)'
            }).parent().elem('stop', {
                offset: '90%',
                'stop-color': 'rgba(105,103,206,0.8)'
            });

            return defs;
    });
})

$win.on('load', function(){
	if (!$('#chart_average_visitors')[0]) {
		return;
	}

	/* Average daily visitors */
	var _chartAverageVisitors = new Chartist.Pie('#chart_average_visitors', {
			series: [100],
			labels: ['iOS']
		}, {
            donut: true,
            labelInterpolationFnc: function (value) {
                return '\ue9d7';
            },
            donutSolid: true,
            total: 100,
            donutWidth: 10,
    })

	_chartAverageVisitors.on('draw', function (data) {
			if (data.type === 'label') {
				if (data.index === 0) {
					data.element.attr({
						dx: data.element.root().width() / 2,
						dy: (data.element.root().height() + (data.element.height() / 4)) / 2,
						class: 'ct-label',
						'font-family': 'feather'
					});
				} else {
					data.element.remove();
				}
			}
	})

	// For the sake of the example we update the chart every time it's created with a delay of 8 seconds
	_chartAverageVisitors.on('created', function (data) {
			var defs = data.svg.querySelector('defs') || data.svg.elem('defs');
			defs.elem('linearGradient', {
				id: 'donutGradient5',
				x1: 0,
				y1: 1,
				x2: 0,
				y2: 0
			}).elem('stop', {
				offset: '0%',
				'stop-color': 'rgba(253,99,107,1)'
			}).parent().elem('stop', {
				offset: '95%',
				'stop-color': 'rgba(253,99,107, 0.3)'
			});
			return defs;
	})
	/* Average daily visitors */
})

$win.on('load', function(){
	/* Month visitors */
	if (!$('#visitor-month-year-chart')[0]) {
		return;
	}

	var lineGradientChart = new Chartist.Line('#visitor-month-year-chart', {
        labels: labelsMonthLogins,
        series: seriesMonthLogins
    }, {
            low: 0,
            fullWidth: true,
            onlyInteger: true,
            axisY: {
                low: 0,
                scaleMinSpace: 30,
				onlyInteger: true,
				labelInterpolationFnc: function (value) {
					if (isKMonthLogins) {
						return (value / 1000) + 'k';
					} else {
						return value;
					}
                }
            },
            axisX: {
                showGrid: false
            },
            lineSmooth: Chartist.Interpolation.simple({
                divisor: 3
            }),
            plugins: [
                Chartist.plugins.tooltip({
                    appendToBody: false,
                    pointClass: 'ct-point-circle-transperent'
                  })
              ]

        });
    lineGradientChart.on('created', function (data) {
        var defs = data.svg.querySelector('defs') || data.svg.elem('defs');
        defs.elem('linearGradient', {
            id: 'linear6',
            x1: 0,
            y1: 1,
            x2: 0,
            y2: 0
        }).elem('stop', {
            offset: 0,
            'stop-color': 'rgba(45,121,255,0.7)'
        }).parent().elem('stop', {
            offset: 1,
            'stop-color': 'rgba(249,81,255, 0.7)'
        });

        defs.elem('linearGradient', {
            id: 'linear7',
            x1: 0,
            y1: 1,
            x2: 1,
            y2: 0
        }).elem('stop', {
            offset: 0,
            'stop-color': 'rgba(247,214,142,1)'
        }).parent().elem('stop', {
            offset: 1,
            'stop-color': 'rgba(248,120,131, 1)'
        });

        return defs;


    }).on('draw', function (data) {
        var circleRadius = 9;
        if (data.type === 'point') {
            var circle = new Chartist.Svg('circle', {
                cx: data.x,
                cy: data.y,
                'ct:value': data.value.y,
                r: circleRadius,
                class: 'ct-point-circle-transperent'//data.value.y === 600 ? 'ct-point-circle' : 'ct-point-circle-transperent'
            });
            data.element.replace(circle);
        }
        if (data.type === 'line') {
            data.element.animate({
                d: {
                    begin: 100,
                    dur: 1000,
                    from: data.path.clone().scale(1, 0).translate(0, data.chartRect.height()).stringify(),
                    to: data.path.clone().stringify(),
                    easing: Chartist.Svg.Easing.easeOutQuint
                }
            });
        }
    });
	/* Month visitors */

})