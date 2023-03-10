#!/usr/bin/env python3

from  coulomb_meter import KgfR50



sample_50 = b':r50=1,233,1349,19,90000,87862,122559,137818,79,0,0,1,0,30000,\r\n'
sample_51 = b':r51=1,27,0,0,0,0,0,100,0,0,900,100,100,100,0,0,1,\r\n'
reading = KgfR50(sample_50)
reading.asCSV()


exit(0)