fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

N = 5
menMeans = (20, 35, 30, 35, 27)
womenMeans = (25, 32, 34, 20, 25)
menStd = (2, 3, 4, 1, 2)
womenStd = (3, 5, 2, 3, 3)
ind = numpy.arange(N)    # the x locations for the groups
width = 0.35       # the width of the bars: can also be len(x) sequence


p1 = ax.bar(ind, menMeans, width, yerr=menStd)
p2 = ax.bar(ind, womenMeans, width,
             bottom=menMeans, yerr=womenStd)

ax.yaxis.set_label('Scores')
ax.set_title('Stacked column chart')
ax.set_xticks(ind)
ax.set_xticklabels(('G1', 'G2', 'G3', 'G4', 'G5'))
ax.set_yticks(numpy.arange(0, 81, 10))
ax.legend((p1[0], p2[0]), ('Men', 'Women'))

fig