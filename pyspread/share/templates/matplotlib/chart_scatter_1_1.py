fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

# Fixing random state for reproducibility
numpy.random.seed(19680801)


N = 50
x1 = numpy.random.rand(N)
y1 = numpy.random.rand(N)

x2 = 0.5 + numpy.random.rand(N) * 2
y2 = numpy.random.rand(N) ** 2

ax.scatter(x1, y1, c='r', alpha=0.5)
ax.scatter(x2, y2, c='b', alpha=0.5)

ax.set(title='Scatter chart', xlabel="X", ylabel="Y")

fig
