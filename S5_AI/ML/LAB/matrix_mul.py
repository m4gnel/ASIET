r1 = int(input("Enter the first row : "))
r2 = int(input("Enter the second row : "))
c1 = int(input("Enter the first column :"))
c2 = int(input("Enter the second column : "))

if c1 != r2:
    print("Matrix multiplication not possible : ")
else:
    print("Matrix A : ")
    a = []
    for i in range(r1):
        row = list(map(int, input().split()))
        a.append(row)
    
    print("Matrix B : \n")
    b = []
    for i in range(r2):
        row = list(map(int, input().split()))
        b.append(row)
    
    result = []
    for i in range(r1):
        row = []
        for j in range(c2):
            s = 0
        for k in range(c1):
            s = s + a[i][k] * b[k][j]
        row.append(s)
        result.append(row)

    for row in result:
        print(*row)
