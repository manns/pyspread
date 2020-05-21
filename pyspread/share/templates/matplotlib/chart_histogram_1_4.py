fig = Figure()
ax = fig.add_axes([.2,.2, .7, .7])

numpy.random.seed(19680801)
number_of_bins = 20

# An example of three data sets to compare
number_of_data_points = 387
labels = ["A", "B", "C"]
data_sets = [numpy.random.normal(0, 1, number_of_data_points),
             numpy.random.normal(6, 1, number_of_data_points),
             numpy.random.normal(-3, 1, number_of_data_points)]

# Computed quantities to aid plotting
hist_range = (numpy.min(data_sets), numpy.max(data_sets))
binned_data_sets = []
for d in data_sets:
    h = numpy.histogram(d, range=hist_range, bins=number_of_bins)[0]
    binned_data_sets.append(h)

binned_maximums = numpy.max(binned_data_sets, axis=1)
x_locations = numpy.arange(0, sum(binned_maximums), numpy.max(binned_maximums))

# The bin_edges are the same for all of the histograms
bin_edges = numpy.linspace(hist_range[0], hist_range[1], number_of_bins + 1)
centers = 0.5 * (bin_edges + numpy.roll(bin_edges, 1))[:-1]
heights = numpy.diff(bin_edges)

# Cycle through and plot each histogram
for x_loc, binned_data in zip(x_locations, binned_data_sets):
    lefts = x_loc - 0.5 * binned_data
    ax.barh(centers, binned_data, height=heights, left=lefts)

ax.set_xticks(x_locations)
ax.set_xticklabels(labels)

ax.set_ylabel("Data values")
ax.set_xlabel("Data sets")

ax.set_title('Multiple vertical histogram charts', pad=15)

fig
