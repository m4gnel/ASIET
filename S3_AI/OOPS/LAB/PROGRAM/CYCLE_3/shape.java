import java.util.*;
abstract class shape
{
	abstract void numberofsides();
	
	
}
class rectangle extends shape
{
	void numberofsides()
	{
		System.out.println("the numberof sides of rectangle is 4");
	}
}
class triangle extends shape
{
	void numberofsides()
	{
		System.out.println("the numberof sides of rectangle is 3");
	}
}
class hexagon extends shape
{
	void numberofsides()
	{
		System.out.println("the numberof sides of rectangle is 6");
	}
}
class main
{
	public static void main(String args[])
	{
		Scanner S= new Scanner(System.in);
		rectangle r=new rectangle();
		r.numberofsides();
		triangle t=new triangle();
		t.numberofsides();
		hexagon h=new hexagon();
		h.numberofsides();
		S.close();
		}
}
