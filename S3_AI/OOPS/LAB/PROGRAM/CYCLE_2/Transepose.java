//program to find transpose of a matrix
//Magnel Olivero
//Roll no:38
import java.util.*;
class transpose
{
	public static void main (String args [])
	{
		int a[][]=new int[50][50];
		int b[][]=new int[50][50];
		Scanner S= new Scanner(System.in);
		System.out.println("enter the size of matrix");
		int r=S.nextInt();
		int c=S.nextInt();
		System.out.println("enter the matrix");
		for(int i=0;i<r;i++)
		{
			for(int j=0;j<c;j++)
			{	System.out.print("a[" + i + "][" + j + "]: ");
				a[i][j]=S.nextInt();
			}
		}
		for(int i=0;i<r;i++)
		{
			for(int j=0;j<c;j++)
			{
				b[j][i]=a[i][j];
			}
		}
		System.out.println("the transpose matrix is");
		for(int i=0;i<c;i++)
		{
			for(int j=0;j<r;j++)
			{
				System.out.print(" "+b[i][j]);
			}
			System.out.println();
		}
		S.close();
}
}


PS C:\Users\devik\java practise> javac transpose.java
PS C:\Users\devik\java practise> java transpose
enter the size of matrix
2
2
enter the matrix
a[0][0]: 1
a[0][1]: 2
a[1][0]: 3
a[1][1]: 4
the transpose matrix is
 1 3
 2 4
PS C:\Users\devik\java practise>
