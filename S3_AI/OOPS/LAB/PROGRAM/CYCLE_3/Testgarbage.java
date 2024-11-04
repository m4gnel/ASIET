public class testgarbage
{
  public void finalize()
  {
   System.out.println("object is garbage collected");
  }
  public static void main(String args[])
  {
    testgarbage s1=new testgarbage();
    testgarbage s2=new testgarbage();
    s1=null;
    s2=null;
    System.gc();
  }
}
