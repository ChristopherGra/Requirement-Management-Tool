import csv
import matplotlib.pyplot as plt

ifile = r"/home/christopher/RM/similarity_debug_output.csv"

with open(ifile, 'r') as debug_file:
    reader = csv.DictReader(debug_file, delimiter=';')

    sim = []
    sim2 = []
    ai_sim = []
    for row in reader:
        sim.append(float(row['similarity']))
        sim2.append(float(row['similarity2']))
        ai_sim.append(float(row['ai_similarity']))

# sort all by sim2
combined = list(zip(sim, sim2, ai_sim))
combined.sort(key=lambda x: x[1], reverse=True)
sim, sim2, ai_sim = zip(*combined)


plt.plot(sim, label='Similarity')
plt.plot(sim2, label='Refined Similarity')
plt.plot(ai_sim, label='AI Similarity')
plt.xlabel('Requirement')
plt.ylabel('Similarity')
plt.title('Similarity vs AI Similarity')
plt.legend()
plt.show()