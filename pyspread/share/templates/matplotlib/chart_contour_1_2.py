from matplotlib import cm

fig = Figure()
ax = fig.add_axes([.15,.15, .75, .75])

origin = 'lower'

delta = 0.025

x = y = numpy.arange(-3.0, 3.01, delta)
X, Y = numpy.meshgrid(x, y)
Z1 = numpy.exp(-X**2 - Y**2)
Z2 = numpy.exp(-(X - 1)**2 - (Y - 1)**2)
Z = (Z1 - Z2) * 2

CS = ax.contourf(X, Y, Z, 10, cmap=cm.bone, origin=origin)

CS2 = ax.contour(CS, levels=CS.levels[::2], colors='r', origin=origin)

ax.set_title('Contour chart', pad=15)
ax.set_xlabel('X')
ax.set_ylabel('Y')

# Make a colorbar for the ContourSet returned by the contourf call.
cbar = fig.colorbar(CS)
cbar.ax.set_ylabel('Z')

# Add the contour line levels to the colorbar
cbar.add_lines(CS2)

fig
