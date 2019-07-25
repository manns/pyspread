fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7], projection='polar')

r = numpy.arange(0, 2, 0.01)
theta = 2 * numpy.pi * r

ax.plot(theta, r)
ax.set_rmax(2)
ax.set_rticks([0.5, 1, 1.5, 2])  # Less radial ticks
ax.set_rlabel_position(-22.5)  # Move radial labels away from plotted line
ax.grid(True)

ax.set(aspect="equal")
ax.set_title("Line plot on polar axis", pad=20)

fig
