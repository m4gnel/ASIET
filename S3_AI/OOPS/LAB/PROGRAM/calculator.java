import javax.swing.*;
import java.awt.*;
import java.awt.event.*;

public class c{

    // Declare the components
    private JFrame frame;
    private JTextField num1Field, num2Field, resultAddField, resultSubtractField, resultMultiplyField, resultDivideField;

    public c() {
        // Create frame for the calculator window
        frame = new JFrame("Simple Calculator");

        // Create text fields for input and results
        num1Field = new JTextField(10);
        num2Field = new JTextField(10);
        resultAddField = new JTextField(10);
        resultSubtractField = new JTextField(10);
        resultMultiplyField = new JTextField(10);
        resultDivideField = new JTextField(10);

        // Set result fields as non-editable (no user input)
        resultAddField.setEditable(false);
        resultSubtractField.setEditable(false);
        resultMultiplyField.setEditable(false);
        resultDivideField.setEditable(false);

        // Set layout for the frame
        frame.setLayout(new GridLayout(6, 2));

        // Add components to the frame
        frame.add(new JLabel("Enter first number:"));
        frame.add(num1Field);
        frame.add(new JLabel("Enter second number:"));
        frame.add(num2Field);
        frame.add(new JLabel("Addition result:"));
        frame.add(resultAddField);
        frame.add(new JLabel("Subtraction result:"));
        frame.add(resultSubtractField);
        frame.add(new JLabel("Multiplication result:"));
        frame.add(resultMultiplyField);
        frame.add(new JLabel("Division result:"));
        frame.add(resultDivideField);

        // Add key listeners to input fields to trigger calculation
        num1Field.addKeyListener(new KeyAdapter() {
            public void keyReleased(KeyEvent e) {
                updateResults();
            }
        });

        num2Field.addKeyListener(new KeyAdapter() {
            public void keyReleased(KeyEvent e) {
                updateResults();
            }
        });

        // Frame settings
        frame.setSize(400, 300);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setLocationRelativeTo(null); // Center the window
        frame.setVisible(true);
    }

    // Method to update results based on input values
    private void updateResults() {
        try {
            // Get values from the text fields
            double num1 = Double.parseDouble(num1Field.getText());
            double num2 = Double.parseDouble(num2Field.getText());

            // Perform the operations and update result fields
            resultAddField.setText(String.valueOf(num1 + num2));
            resultSubtractField.setText(String.valueOf(num1 - num2));
            resultMultiplyField.setText(String.valueOf(num1 * num2));

            if (num2 != 0) {
                resultDivideField.setText(String.valueOf(num1 / num2));
            } else {
                resultDivideField.setText("Error: Div by 0");
            }
        } catch (NumberFormatException e) {
            // If the user enters invalid input, clear the result fields
            resultAddField.setText("");
            resultSubtractField.setText("");
            resultMultiplyField.setText("");
            resultDivideField.setText("");
        }
    }

    public static void main(String[] args) {
        // Run the calculator
        new CalculatorWithoutSwitch();
    }
}
