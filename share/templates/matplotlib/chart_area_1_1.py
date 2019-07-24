fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

# Data for plotting
t = numpy.arange(0.0, 2.0, 0.01)
s = 1 + numpy.sin(2 * numpy.pi * t)

ax.plot(t, s)
ax.fill_between(t, 0, s, facecolor='blue', alpha=0.5)

ax.set_xlim(0, 2)
ax.set_ylim(0, None)

ax.set(xlabel='Time (s)', ylabel='Voltage (mV)',
       title='Area chart')
ax.grid()

fig
