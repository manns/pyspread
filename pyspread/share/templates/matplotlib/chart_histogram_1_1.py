fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

N_points = 100000
n_bins = 20

# Fixing random state for reproducibility
numpy.random.seed(19680801)

# Generate a normal distribution
x = numpy.random.randn(N_points)

# We can set the number of bins with the `bins` kwarg
ax.hist(x, bins=n_bins)

ax.set(xlabel='Value', ylabel='Frequency',
       title='Histogram chart')

fig
