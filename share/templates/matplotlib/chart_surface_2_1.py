from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

fig = Figure()
ax = fig.add_subplot(111, projection='3d')

X = numpy.arange(-5, 5, 0.25)
Y = numpy.arange(-5, 5, 0.25)
X, Y = numpy.meshgrid(X, Y)
R = numpy.sqrt(X**2 + Y**2)
Z = numpy.sin(R)

ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.viridis)

ax.set_xlabel('X', labelpad=5)
ax.set_ylabel('Y', labelpad=5)
ax.set_zlabel('Z', labelpad=5)
ax.tick_params('x', pad=0)
ax.tick_params('y', pad=0)
ax.tick_params('z', pad=3)

ax.set_title("Surface chart", pad=20)

fig