# Replicating web-based Blat parameters in command-line version

c.f.:
 + https://genome.ucsc.edu/FAQ/FAQblat.html
 + https://genome.ucsc.edu/goldenPath/help/blatSpec.html
 + https://genome.ucsc.edu/goldenPath/help/blatSpec.html#gfServerUsage

```{sh}
SMEDSXL41=/microarray/repo/cws/schMed/schMedSxl41/SmedSxl_genome_v41.2bit
SMEDSXL31=/microarray/repo/cws/schMed/schMedSxl31/SmedSxl_genome_v31.2bit
gfServer start blatMachine 33333 -stepSize=5 -log=/var/log/blatServerCi1.log ${SMEDSXL41}
```
