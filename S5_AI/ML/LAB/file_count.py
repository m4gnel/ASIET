filename = input("Enter the filename: ")
with open(filename, 'r') as file:
    text = file.read().lower()
    words = text.split()
    d = {}
    for word in words:
        if word in d:
            d[word] += 1
        else:
            d[word] = 1

max_used = max(d, key=d.get)
print("Most frequent word:", max_used)
print("Frequency:", d[max_used])
