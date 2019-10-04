fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

N_points = 100000
n_bins = 20

# Fixing random state for reproducibility
numpy.random.seed(19680801)

# Generate a normal distribution, center at x=0 and y=5
x = numpy.random.randn(N_points)
y = .4 * x + numpy.random.randn(100000) + 5

# We can set the number of bins with the `bins` kwarg
# We can also define custom numbers of bins for each axis
ax.hist2d(x, y, bins=(50,30))

ax.set(xlabel='X', ylabel='Y')
ax.set_title('Matrix chart', pad=20)

fig
