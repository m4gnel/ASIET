import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
class test implements ActionListener
{
	JLabel l1,l2;
	JTextField t1,t2;
	JButton b1,b2;
	test()
	{
		JFrame f=new JFrame("textfield");
		l1=new JLabel("user name");
		t1=new JTextField(22);
		l2=new JLabel("password");
		t2=new JTextField(20);
		b1=new JButton("submit");
		//b2=new JButton("submit");
		b1.addActionListener(this);
		JPanel p=new JPanel(new GridLayout(6,1));
		p.add(l1);
		p.add(t1);
		p.add(b1);
		b2=new JButton("clear");
		p.add(l2);
		p.add(t2);
		p.add(b2);
		b1.addActionListener(this);
		b2.addActionListener(this);
		f.add(p);
		f.setSize(300,300);
		f.show();
	}
	public void actionPerformed(ActionEvent e)
	{
		String s=e.getActionCommand();
		if(s.equals("submit"));
		{
			l1.setText(t1.getText());
			//t1.setText(" ");
			l2.setText(t2.getText());
			//t2.setText(" ");
		}
	}
	public static void main(String args[])
	{
		test t1=new test();
		test t2=new test();
	}
}
