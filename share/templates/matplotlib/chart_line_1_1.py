fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

# Data for plotting
t = numpy.arange(0.0, 2.0, 0.01)
s = 1 + numpy.sin(2 * numpy.pi * t)

ax.plot(t, s)

ax.set(xlabel='time (s)', ylabel='voltage (mV)',
       title='Line plot')
ax.grid()

fig
