from mpl_toolkits.axes_grid1 import make_axes_locatable

fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

# Fixing random state for reproducibility
numpy.random.seed(19680801)


# the random data
x = numpy.random.randn(1000)
y = numpy.random.randn(1000)


# the scatter plot:
ax.scatter(x, y, alpha=0.08)
ax.set_aspect(1.)

# create new axes on the right and on the top of the current axes
# The first argument of the new_vertical(new_horizontal) method is
# the height (width) of the axes to be created in inches.
divider = make_axes_locatable(ax)
axHistx = divider.append_axes("top", 0.6, pad=0.1, sharex=ax)
axHisty = divider.append_axes("right", 0.6, pad=0.1, sharey=ax)

# Make some labels invisible
axHistx.xaxis.set_tick_params(labelbottom=False)
axHisty.yaxis.set_tick_params(labelleft=False)

# Determine nice limits by hand:
binwidth = 0.25
xymax = max(numpy.max(numpy.abs(x)), numpy.max(numpy.abs(y)))
lim = (int(xymax/binwidth) + 1)*binwidth

bins = numpy.arange(-lim, lim + binwidth, binwidth)
axHistx.hist(x, bins=bins)
axHisty.hist(y, bins=bins, orientation='horizontal')

# the xaxis of axHistx and yaxis of axHisty are shared with axScatter,
# thus there is no need to manually adjust the xlim and ylim of these
# axis.

axHistx.set_yticks([0, 50, 100])

axHisty.set_xticks([0, 50, 100])

ax.set(xlabel="X", ylabel="Y")
ax.set_title('Scatter histogram chart', pad=70)

fig
