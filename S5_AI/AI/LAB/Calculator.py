a = int(input("Enter first number : "))
b = int(input("Enter second number : "))
o = input("Enter the operation to perform : ")
if(o == "+"):
	print("Addition : ", a + b)
elif(o == "-"):
	print("Subtraction : ", a - b)
elif(o == "*"):
	print("Multiplication : ", a * b)
elif(o == "/"):
	print("Division : ", a/b)
else:
	print("Invalid operation.")
