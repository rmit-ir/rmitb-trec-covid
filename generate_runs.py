import subprocess
import operator
import sys

topic_count=int(sys.argv[1]) # 30
system_count=int(sys.argv[2]) # 16
uqv_count=int(sys.argv[3]) # 10

paths = [line[2:] for line in subprocess.check_output("find . -name *.res", shell=True).splitlines()]

runs = dict()

def do_min_max(runs, runid, uqvid, maxscore, minscore):
    for i in range(len(runs[runid][uqvid])):
        score = runs[runid][uqvid][i][1]
        z = (score - minscore) / (maxscore - minscore)
        runs[runid][uqvid][i][1] = z
    
# load all the runs into memory and minmax score them
runid = 0
for path in paths:
    print(path)
    runs[runid] = dict() 
    with open(path) as f:
        linecount = 1
        maxscore = 0.0
        minscore = 0.0
        current_uqvid = ""
        for line in f:
            spl = line.split()
            uqvid = spl[0]
            docid = spl[2]
            rank = int(spl[3])
            score = float(spl[4])

            if current_uqvid == "":
                current_uqvid = uqvid
                maxscore = score
                runs[runid][uqvid] = []

            if current_uqvid != uqvid and rank == 0:
                do_min_max(runs, runid, current_uqvid, maxscore, minscore)
                
                maxscore = score
                current_uqvid = uqvid
                runs[runid][uqvid] = []
            else:
                minscore = score

            runs[runid][uqvid].append([docid, score])
            
    runid += 1

# iterate over each topic and fuse

f = open("RMITBFuseM2", "w")
# have same form as before even though only one run so we can reuse min max
fusedruns = dict()
fusedruns[0] = dict()

for topic in range(1, topic_count + 1):
    print(str(topic))
    fusedruns[0][topic] = []
    docscores = dict()
    for uqv in range(1, uqv_count):
        for runid in range(0, system_count - 1):
            for pair in runs[runid][str(topic) + "-" + str(uqv)]:
                if pair[0] in docscores:
                    docscores[pair[0]] += pair[1]
                else:
                    docscores[pair[0]] = pair[1]
            print(topic)

    sorted_docscores = sorted(docscores.items(), key=operator.itemgetter(1), reverse=True)
    rank = 0
    maxscore = 0
    for pair in sorted_docscores:
        if rank == 0:
            maxscore = pair[1]

        f.write(str(topic) + " Q0 " + str(pair[0]) + " " + str(rank) + " " + str(pair[1]) + " RMITBFuseM2\n" )
        fusedruns[0][topic].append([pair[0], pair[1]])

        if rank == 999:
            do_min_max(fusedruns, 0, topic, maxscore, pair[1])
            break
        rank += 1

f.close()

days = dict()
with open("../dayssince.csv") as f:
    for line in f:
        sp = line.split(",")
        days[sp[0]] = int(sp[1])

def do_adjust(runs, runid, uqvid):
    for i in range(len(runs[runid][uqvid])):
        score = runs[runid][uqvid][i][1]
        doc = runs[runid][uqvid][i][0]
        dayssince = days[doc]
        # ab-exponential regression from points (0, 1) and (120 days, 0.01)
        modifier = 1 * (0.9623506264 ** dayssince)
        z = score + modifier
        runs[runid][uqvid][i][1] = z
 
t = open("RMITBM1", "w")
for topic in range(1, topic_count + 1):
    do_adjust(fusedruns, 0, topic)
    sorted_fusedruns_t = sorted(fusedruns[0][topic], key=operator.itemgetter(1), reverse=True)
    rank = 0
    for pair in sorted_fusedruns_t:
        t.write(str(topic) + " Q0 " + str(pair[0]) + " " + str(rank) + " " + str(pair[1]) + " RMITBM1\n" )
        rank += 1
