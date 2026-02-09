s = input("Enter the string : ")
f = {}
s = s.split()
for words in s :
	if words in f:
		f[words] += 1
	else:
		f[words] = 1
for words,count in f.items():
	print(words,count)
		
