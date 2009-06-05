set term png size 1400,750 enhanced
set output 'noise.png'
set autoscale yfix
set xdata time
set timefmt '%s'
set format x '%Y-%m-%d %H:%M'
set ylabel 'noise'
set xtics rotate 600
set grid
set datafile separator ' '
# plot 'output.txt' using 1:2 notitle with points
plot "< cat *.noise" using 1:2 notitle with boxes
