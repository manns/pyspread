from matplotlib import cm

fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

size = 0.3
vals = numpy.array([[60., 32.], [37., 40.], [29., 10.]])

cmap = cm.tab20c
outer_colors = cmap(numpy.arange(3)*4)
inner_colors = cmap(numpy.array([1, 2, 5, 6, 9, 10]))

ax.pie(vals.sum(axis=1), radius=1, colors=outer_colors,
       wedgeprops=dict(width=size, edgecolor='w'))

ax.pie(vals.flatten(), radius=1-size, colors=inner_colors,
       wedgeprops=dict(width=size, edgecolor='w'))

ax.set(aspect="equal", title="Pie ring chart")

fig
