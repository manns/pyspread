fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

# Fixing random state for reproducibility
numpy.random.seed(19680801)

spread = numpy.random.rand(50) * 100
center = numpy.ones(25) * 50
flier_high = numpy.random.rand(10) * 100 + 100
flier_low = numpy.random.rand(10) * -100
data = numpy.concatenate((spread, center, flier_high, flier_low))

spread = numpy.random.rand(50) * 100
center = numpy.ones(25) * 40
flier_high = numpy.random.rand(10) * 100 + 100
flier_low = numpy.random.rand(10) * -100
d2 = numpy.concatenate((spread, center, flier_high, flier_low))

data.shape = (-1, 1)
d2.shape = (-1, 1)

data = [data, d2, d2[::2, 0]]

# Multiple box plots on one Axes
ax.boxplot(data)

ax.set(xlabel='Data series', ylabel='Value',
       title='Boxplot chart')

fig
