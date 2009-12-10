reset
set term png size 1024,600 enhanced
set output "noise.png"
set style data lines
set datafile separator ','
set timefmt "%s"
set format x "%Y-%m-%d %H:%M"
set xdata time
set ylabel "Noise level"
set grid
set xtics rotate 90
set key left

plot "< sqlite3 -csv noise.db 'SELECT * FROM noise'" using 1:2 with lines linetype 1 lw 1 title "Noise in our livingroom"
