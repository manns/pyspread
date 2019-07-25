fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

# Fixing random state for reproducibility
numpy.random.seed(19680801)


N = 50
x = numpy.random.rand(N)
y = numpy.random.rand(N)
colors = numpy.random.rand(N)
area = (30 * numpy.random.rand(N))**2  # 0 to 15 point radii

ax.scatter(x, y, s=area, c=colors, alpha=0.5)

ax.set(title='Bubble chart', xlabel="X", ylabel="Y")

fig
