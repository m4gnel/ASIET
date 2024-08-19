//program to find the frequency of characters in a string
//Magnel Olivero
//Roll no:38
import java.util.*;
class frequency
{
	public static void main(String args[])
		{  
		   int count=0;
			Scanner S=new Scanner(System.in);
			System.out.println("enter the string");
			String sr;
			sr=S.nextLine();
			sr.toLowerCase();
			System.out.println("enter the character to check");
		   char c= S.next().charAt(0);
		   int len=sr.length();
		   for(int i=0;i<len;i++)
		   {
		   	if(sr.charAt(i)== c)
		   	{
		   	 
		   	
		   		count++;
		   	
		   	}
		   }
		   System.out.println("the frequency of character is"+count);
		   S.close();
		   }
}
