import java.util.*;
class matrixsum
{
	public static void main (String args[])
	{
	int a[][]=new int [50][50];
	int b[][]=new int [50][50];
	int c[][]=new int [50][50];
	int i,j;
	Scanner S=new Scanner(System.in);
	System.out.println("ENTER THE SIZE");
	int m=S.nextInt();
	int n=S.nextInt();
	System.out.println("enter the first array");
	for (i=0;i<m;i++)
	{
		for(j=0;j<n;j++)
		{
		  a[i][j]=S.nextInt();
		}
	}	
	System.out.println("enter the second array");
	for (i=0;i<m;i++)
	{
		for(j=0;j<n;j++)
		{
		   b[i][j]=S.nextInt();
		}
	}	
	
	for (i=0;i<m;i++)
	{
		for(j=0;j<n;j++)
		{
		  c[i][j]=a[i][j]+b[i][j];
		}
	}	

	for (i=0;i<m;i++)
	{
		for(j=0;j<n;j++)
		{
		 System.out.println("the sum is:"+c[i][j]);
		}
	}
	S.close();
	}
}	
	
	
